# Maintainer Intelligence

Analyze open GitHub issues and recommend the few actions a maintainer should consider first.

Return JSON only:

```json
{
  "priorities": [
    {
      "issue_number": 42,
      "title": "Issue title",
      "priority_score": 8.5,
      "reason": "Specific evidence and why this should be handled soon.",
      "user_impact": "Who is affected and how severe it is.",
      "estimated_effort": "low"
    }
  ],
  "missing_info_issues": [12, 34],
  "summary": "Short maintainer-facing overview."
}
```

Rules:

- Recommend fewer high-quality items instead of filling a quota.
- Every priority needs concrete evidence.
- Do not recommend clearly off-topic feature requests.
- Mark vague reports as missing information instead of pretending they are actionable.

