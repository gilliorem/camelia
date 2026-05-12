<?php
declare(strict_types=1);

$root = __DIR__;
$leadsPath = $root . '/data/leads.json';
$repsPath = $root . '/data/sales_reps.json';

function read_json(string $path): array {
    if (!is_file($path)) {
        return [];
    }
    $raw = file_get_contents($path);
    $data = json_decode($raw ?: '[]', true);
    return is_array($data) ? $data : [];
}

$leads = read_json($leadsPath);
$reps = read_json($repsPath);
$repNames = [];
foreach ($reps as $rep) {
    $repNames[$rep['id']] = $rep['first_name'] . ' ' . $rep['last_name'];
}

$statusCounts = ['picked' => 0, 'sent' => 0, 'booked' => 0];
$repCounts = [];
foreach ($leads as $lead) {
    $status = $lead['status'] ?? 'picked';
    if (!array_key_exists($status, $statusCounts)) {
        $statusCounts[$status] = 0;
    }
    $statusCounts[$status]++;
    $repId = $lead['rep_id'] ?? 'unknown';
    if (!array_key_exists($repId, $repCounts)) {
        $repCounts[$repId] = 0;
    }
    $repCounts[$repId]++;
}

usort($leads, function ($a, $b) {
    return strcmp((string)($b['picked_at'] ?? ''), (string)($a['picked_at'] ?? ''));
});

$recent = array_slice($leads, 0, 8);
$rawJson = json_encode($leads, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);
if ($rawJson === false) {
    $rawJson = '[]';
}
?>
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Camelia dashboard</title>
  <style>
    :root {
      --bg: #f3efe7;
      --panel: #ffffff;
      --text: #16302b;
      --muted: #5b6b67;
      --accent: #2d6a4f;
      --accent-2: #c97b3b;
      --line: rgba(22, 48, 43, 0.12);
    }
    body {
      margin: 0;
      font-family: Inter, "Segoe UI", Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(45, 106, 79, 0.16), transparent 30%),
        radial-gradient(circle at top right, rgba(201, 123, 59, 0.16), transparent 28%),
        linear-gradient(180deg, #f8f4ed 0%, var(--bg) 100%);
      color: var(--text);
    }
    .wrap {
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 48px;
    }
    .hero {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      justify-content: space-between;
      align-items: end;
      margin-bottom: 24px;
    }
    h1 {
      margin: 0;
      font-size: 34px;
      letter-spacing: -0.03em;
    }
    .sub {
      margin-top: 8px;
      color: var(--muted);
    }
    .cards {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 14px;
      margin: 18px 0 24px;
    }
    .card {
      background: rgba(255,255,255,0.8);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 18px;
      box-shadow: 0 12px 28px rgba(22, 48, 43, 0.06);
    }
    .card .label {
      color: var(--muted);
      font-size: 13px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .card .value {
      font-size: 36px;
      font-weight: 700;
      margin-top: 10px;
      color: var(--accent);
    }
    .grid {
      display: grid;
      grid-template-columns: 1.5fr 1fr;
      gap: 16px;
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 18px;
      box-shadow: 0 16px 30px rgba(22, 48, 43, 0.05);
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
      font-size: 14px;
    }
    th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    code {
      background: #f3f1eb;
      border-radius: 999px;
      padding: 3px 8px;
    }
    .status {
      display: inline-flex;
      gap: 6px;
      align-items: center;
      font-size: 13px;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--accent-2);
    }
    details {
      margin-top: 14px;
    }
    pre {
      white-space: pre-wrap;
      word-break: break-word;
      font-size: 12px;
      background: #101b18;
      color: #d9efe7;
      border-radius: 16px;
      padding: 16px;
      overflow: auto;
    }
    @media (max-width: 860px) {
      .grid { grid-template-columns: 1fr; }
      h1 { font-size: 28px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="hero">
      <div>
        <h1>Camelia lead dashboard</h1>
        <div class="sub">Tiny JSON-backed view of the current lead database.</div>
      </div>
      <div class="status"><span class="dot"></span> Live from <code>data/leads.json</code></div>
    </div>

    <div class="cards">
      <div class="card"><div class="label">Total leads</div><div class="value"><?= count($leads) ?></div></div>
      <div class="card"><div class="label">Picked</div><div class="value"><?= (int)$statusCounts['picked'] ?></div></div>
      <div class="card"><div class="label">Sent</div><div class="value"><?= (int)$statusCounts['sent'] ?></div></div>
      <div class="card"><div class="label">Booked</div><div class="value"><?= (int)$statusCounts['booked'] ?></div></div>
    </div>

    <div class="grid">
      <div class="panel">
        <h2 style="margin-top:0">Recent leads</h2>
        <table>
          <thead>
            <tr>
              <th>Lead</th>
              <th>Rep</th>
              <th>Status</th>
              <th>Token</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($recent as $lead): ?>
            <tr>
              <td>
                <strong><?= htmlspecialchars((string)($lead['lead_name'] ?? 'Unknown')) ?></strong><br>
                <span style="color:#5b6b67"><?= htmlspecialchars((string)($lead['lead_city'] ?? '')) ?></span>
              </td>
              <td><?= htmlspecialchars($repNames[$lead['rep_id']] ?? (string)($lead['rep_id'] ?? 'unknown')) ?></td>
              <td><code><?= htmlspecialchars((string)($lead['status'] ?? 'picked')) ?></code></td>
              <td><code><?= htmlspecialchars((string)($lead['token'] ?? '')) ?></code></td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$recent): ?>
            <tr><td colspan="4" style="color:#5b6b67">No leads yet. Run the demo pipeline first.</td></tr>
            <?php endif; ?>
          </tbody>
        </table>
      </div>

      <div class="panel">
        <h2 style="margin-top:0">By rep</h2>
        <table>
          <thead>
            <tr>
              <th>Rep</th>
              <th>Leads</th>
            </tr>
          </thead>
          <tbody>
            <?php foreach ($repCounts as $repId => $count): ?>
            <tr>
              <td><?= htmlspecialchars($repNames[$repId] ?? $repId) ?></td>
              <td><strong><?= (int)$count ?></strong></td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$repCounts): ?>
            <tr><td colspan="2" style="color:#5b6b67">No rep assignments yet.</td></tr>
            <?php endif; ?>
          </tbody>
        </table>

        <details>
          <summary style="cursor:pointer;margin-top:16px;color:#2d6a4f;font-weight:600">Raw JSON</summary>
          <pre><?= htmlspecialchars($rawJson) ?></pre>
        </details>
      </div>
    </div>
  </div>
</body>
</html>
