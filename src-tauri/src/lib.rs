use std::path::PathBuf;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;

#[cfg(unix)]
use std::os::unix::process::CommandExt;

use tauri::{Manager, WindowEvent};

#[derive(Default)]
struct BackendProcess(Mutex<Option<Child>>);

fn stop_backend(child: &mut Child) {
    #[cfg(unix)]
    {
        // PyInstaller --onefile uses a bootloader parent plus the Python
        // service child. Killing only the direct child leaves the service
        // listening on 8765 after the desktop window exits. The backend is
        // launched in its own process group, so terminate the entire tree.
        unsafe {
            libc::killpg(child.id() as libc::pid_t, libc::SIGKILL);
        }
        let _ = child.wait();
    }
    #[cfg(not(unix))]
    {
        let _ = child.kill();
        let _ = child.wait();
    }
}

fn stop_managed_backend<R: tauri::Runtime, M: Manager<R>>(manager: &M) {
    if let Ok(mut process) = manager.state::<BackendProcess>().0.lock() {
        if let Some(child) = process.as_mut() {
            stop_backend(child);
        }
        *process = None;
    }
}

fn packaged_backend_path() -> Result<PathBuf, String> {
    let executable = std::env::current_exe()
        .map_err(|error| format!("could not locate desktop executable: {error}"))?;
    let directory = executable
        .parent()
        .ok_or_else(|| "desktop executable has no parent directory".to_string())?;
    let file_name = if cfg!(windows) {
        "github-engineer-backend.exe"
    } else {
        "github-engineer-backend"
    };
    let candidates = [
        directory.join(file_name),
        directory.join("../Resources").join(file_name),
        directory.join("resources").join(file_name),
    ];
    candidates
        .into_iter()
        .find(|candidate| candidate.is_file())
        .ok_or_else(|| format!("packaged backend sidecar {file_name} was not found"))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app = tauri::Builder::default()
        .manage(BackendProcess::default())
        .setup(|app| {
            if !cfg!(debug_assertions) {
                let backend = packaged_backend_path()?;
                let data_dir = app.path().app_data_dir().map_err(|error| {
                    format!("could not locate application data directory: {error}")
                })?;
                std::fs::create_dir_all(&data_dir).map_err(|error| {
                    format!("could not create application data directory: {error}")
                })?;
                let config = data_dir.join(".ghe").join("config.yml");
                if !config.exists() {
                    let config_directory = config
                        .parent()
                        .ok_or_else(|| "desktop config has no parent directory".to_string())?;
                    std::fs::create_dir_all(config_directory).map_err(|error| {
                        format!("could not create desktop config directory: {error}")
                    })?;
                    // A fresh desktop install should be useful without asking
                    // for an API key that the user may not have. Both model
                    // paths reuse the authenticated local Codex/ChatGPT login;
                    // the UI can switch providers later without overwriting
                    // this file behind the user's back.
                    std::fs::write(
                        &config,
                        "model:\n  provider: codex_cli\n  model_name: codex-default\n\n\
                         github:\n  token: ${GITHUB_TOKEN}\n\n\
                         coding_agent:\n  provider: codex_cli\n\n\
                         output:\n  format: markdown\n  output_dir: reports\n  title: 'Maintainer Brief - {date}'\n\n\
                         analysis:\n  lookback_days: 7\n  top_n: 3\n  min_issue_age_hours: 24\n  max_issues_for_llm: 50\n\n\
                         repair:\n  allow_host_verification: false\n",
                    )
                    .map_err(|error| format!("could not write desktop starter config: {error}"))?;
                }
                let mut command = Command::new(backend);
                command
                    .arg("--serve")
                    .args(["--serve-host", "127.0.0.1"])
                    .arg("--config")
                    .arg(config)
                    .current_dir(data_dir)
                    .stdin(Stdio::null())
                    .stdout(Stdio::null())
                    .stderr(Stdio::null());
                #[cfg(unix)]
                command.process_group(0);
                let child = command
                    .spawn()
                    .map_err(|error| format!("could not start packaged backend: {error}"))?;
                *app.state::<BackendProcess>()
                    .0
                    .lock()
                    .map_err(|_| "desktop backend process lock was poisoned".to_string())? =
                    Some(child);
            }
            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, WindowEvent::Destroyed) {
                stop_managed_backend(window);
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building GitHub Engineer");
    app.run(|app_handle, event| {
        if matches!(
            event,
            tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit
        ) {
            stop_managed_backend(app_handle);
        }
    });
}
