<?php
// Camelia booking endpoint. Expects GET /book.php?t=<token>&s=<YYYY-MM-DD>_<slot_id>
// Files expected next to this script:
//   data/leads.json
//   data/sales_reps.json
//   data/schedules/<rep_id>.json
//
// Side effects on success: marks the lead "booked" and the rep slot "busy".

declare(strict_types=1);
date_default_timezone_set('Europe/Paris');

$DATA = __DIR__ . '/data';
$LEADS = $DATA . '/leads.json';
$REPS  = $DATA . '/sales_reps.json';

function bail(string $title_fr, string $msg_fr, string $title_en, string $msg_en, int $http = 400): void {
    http_response_code($http);
    render_page($title_fr, $msg_fr, $title_en, $msg_en, false);
    exit;
}

function read_json(string $path): array {
    $fp = fopen($path, 'r');
    if (!$fp) { throw new RuntimeException("cannot open $path"); }
    flock($fp, LOCK_SH);
    $raw = stream_get_contents($fp);
    flock($fp, LOCK_UN);
    fclose($fp);
    return json_decode($raw, true);
}

function write_json_atomic(string $path, array $data): void {
    $tmp = $path . '.tmp';
    file_put_contents($tmp, json_encode($data, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE) . "\n", LOCK_EX);
    rename($tmp, $path);
}

function render_page(string $title_fr, string $msg_fr, string $title_en, string $msg_en, bool $ok): void {
    $color = $ok ? '#2d6a4f' : '#a63d40';
    header('Content-Type: text/html; charset=utf-8');
    echo <<<HTML
<!doctype html>
<html><head><meta charset="utf-8"><title>$title_fr · $title_en</title></head>
<body style="margin:0;background:#f6f7f8;font-family:Arial,sans-serif;color:#222;">
<div style="max-width:520px;margin:48px auto;padding:32px;background:#fff;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,0.06);">
  <h1 style="color:$color;margin:0 0 12px;">$title_fr</h1>
  <p>$msg_fr</p>
  <hr style="border:none;border-top:1px solid #ddd;margin:24px 0;">
  <h2 style="color:$color;margin:0 0 12px;">$title_en</h2>
  <p>$msg_en</p>
  <p style="margin-top:32px;color:#888;font-size:13px;">L'équipe Lumélio · The Lumélio team</p>
</div>
</body></html>
HTML;
}

// --- 1. Validate inputs ---
$token = $_GET['t'] ?? '';
$slot  = $_GET['s'] ?? '';
if (!preg_match('/^[a-f0-9]{8}$/', $token) || !preg_match('/^\d{4}-\d{2}-\d{2}_[a-z0-9-]+$/', $slot)) {
    bail('Lien invalide', "Ce lien de réservation n'est pas valide.",
         'Invalid link', 'This booking link is not valid.');
}
[$slot_date, $slot_id] = [substr($slot, 0, 10), substr($slot, 11)];

// --- 2. Find the lead ---
$leads = read_json($LEADS);
$lead_idx = null;
foreach ($leads as $i => $l) {
    if ($l['token'] === $token) { $lead_idx = $i; break; }
}
if ($lead_idx === null) {
    bail('Lien expiré', 'Ce lien de réservation est introuvable ou a expiré.',
         'Link expired', 'This booking link could not be found or has expired.', 404);
}
$lead = $leads[$lead_idx];

// --- 3. Already booked? Show idempotent confirmation ---
if ($lead['status'] === 'booked') {
    $b = $lead['booked_slot'];
    render_page(
        'Rendez-vous déjà confirmé',
        "Votre rendez-vous est déjà réservé pour le <strong>" . htmlspecialchars($b) . "</strong>. À très bientôt !",
        'Appointment already confirmed',
        "Your appointment is already booked for <strong>" . htmlspecialchars($b) . "</strong>. See you soon!",
        true
    );
    exit;
}

// --- 4. Verify the slot is still free in the rep schedule ---
$rep_id = $lead['rep_id'];
$sched_path = $DATA . '/schedules/' . $rep_id . '.json';
$schedule = read_json($sched_path);
$slot_idx = null;
foreach ($schedule as $i => $s) {
    if ($s['date'] === $slot_date && $s['slot_id'] === $slot_id) { $slot_idx = $i; break; }
}
if ($slot_idx === null) {
    bail('Créneau introuvable', "Ce créneau n'existe pas dans l'agenda.",
         'Slot not found', 'This slot does not exist in the schedule.', 404);
}
if ($schedule[$slot_idx]['status'] !== 'free') {
    bail('Créneau déjà pris',
         "Désolé, ce créneau vient d'être réservé. Répondez à notre email pour en choisir un autre.",
         'Slot already taken',
         "Sorry, that slot was just taken. Reply to our email and we'll offer another time.", 409);
}

// --- 5. Reserve: mark schedule busy + lead booked ---
$schedule[$slot_idx]['status'] = 'busy';
$leads[$lead_idx]['status'] = 'booked';
$leads[$lead_idx]['booked_slot'] = $slot_date . '_' . $slot_id;
$leads[$lead_idx]['booked_at']   = date('c');
write_json_atomic($sched_path, $schedule);
write_json_atomic($LEADS, $leads);

// --- 6. Look up rep for nicer message ---
$reps = read_json($REPS);
$rep_name = $rep_id;
foreach ($reps as $r) { if ($r['id'] === $rep_id) { $rep_name = $r['first_name'] . ' ' . $r['last_name']; break; } }

$s = $schedule[$slot_idx];
$human = htmlspecialchars($slot_date . ' · ' . $s['start'] . '–' . $s['end']);
render_page(
    'Rendez-vous confirmé !',
    "Vous rencontrerez <strong>" . htmlspecialchars($rep_name) . "</strong> le <strong>$human</strong>. Vous recevrez un email de confirmation séparément.",
    'Appointment confirmed!',
    "You'll meet <strong>" . htmlspecialchars($rep_name) . "</strong> on <strong>$human</strong>. A confirmation email will follow.",
    true
);
