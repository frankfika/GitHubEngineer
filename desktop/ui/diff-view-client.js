// CodeMirror 6 entry point for GitHubEngineer's diff view.
//
// This file exists so the importmap (injected by ``app.js``) is in scope
// when the module is evaluated.  We re-export only the symbols the
// diff renderer actually uses; keeping the surface narrow avoids
// pulling in @codemirror/commands / @codemirror/search and the rest
// of the bundle we do not need.
//
// Why we ship this as a separate module instead of inlining in app.js:
//   - The 5 prototype traps (see README §6) all stem from importmap
//     timing.  An ``<script type="importmap">`` must be in the
//     document **before** any module script that uses bare specifiers
//     is fetched.  A separate module loaded via ``import()`` after the
//     importmap is in the DOM is the cleanest way to honour that.
//   - The file size is small (~3 KB) so loading on first diff view is
//     a one-time cost; a cached CodeMirror is not worth the complexity
//     for a sub-page that may never open.

export {
  EditorView,
  lineNumbers,
  highlightActiveLine,
  highlightActiveLineGutter,
  Decoration,
} from "@codemirror/view";

export {
  EditorState,
  StateField,
  StateEffect,
  RangeSetBuilder,
} from "@codemirror/state";
