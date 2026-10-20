<#
.SYNOPSIS
  Trascrivi-Cartella.ps1 - trascrive le registrazioni di una cartella lasciando ogni cosa dentro quella cartella.

.DESCRIPTION
  Percorre le registrazioni sotto la cartella delle sorgenti, salta i file che corrispondono
  agli schemi personali PRIMA di aprirli, salta quelli gia' trascritti e completi, e scrive le
  trascrizioni nella cartella di uscita rispecchiando l'albero delle sottocartelle. E'
  riprendibile: rilanciarlo riparte da dove si era fermato, e rifa' da capo una trascrizione
  rimasta a meta' invece di scambiarla per lavoro finito. Ogni corsa lascia una riga per file
  in <uscita>/_strumenti/registro-corse.log.

  Copia generica, versionata nel progetto, dello strumento nato per un corpus su disco esterno:
  l'originale vive accanto al materiale e sparisce con esso quando il disco si scollega, questa
  resta. Nessun percorso di quel corpus e' predefinito qui: -Radice e' obbligatorio.

.EXAMPLE
  powershell -NoProfile -ExecutionPolicy Bypass -File tools/Trascrivi-Cartella.ps1 -Radice "X:/corpus" -SoloPiano
#>
param(
  [Parameter(Mandatory = $true)][string]$Radice,
  [string]$Sorgenti   = "REGISTRAZIONI",
  [string]$Uscita     = "TRASCRIZIONI",
  [string]$Modello    = "small",
  [string]$Lingua     = "it",
  [string]$Formati    = "txt,srt,json",
  [string]$Vad        = "silero",
  [string]$Transcribe = "transcribe",
  [string]$Esclusi    = "",
  [string]$Ffprobe    = "C:/Users/Utente/AppData/Local/Microsoft/WinGet/Links/ffprobe.exe",
  [switch]$CancellaVideo,
  [ValidateSet("", "si", "no")][string]$Sovrascrittura = "",
  [string]$Python     = "python",
  [string]$Sovrascrivi = "tools/sovrascrivi.py",
  [double]$SogliaCopertura = 0.97,
  [int]$Quanti        = 0,
  [switch]$SoloPiano
)

$ErrorActionPreference = "Stop"
$estensioni = @(".mp4", ".mkv", ".mov", ".avi", ".m4a", ".mp3", ".wav", ".webm")

$cartellaSorgenti = Join-Path $Radice $Sorgenti
$cartellaUscita   = Join-Path $Radice $Uscita
$cartellaStrum    = Join-Path $cartellaUscita "_strumenti"
if (-not $Esclusi) { $Esclusi = Join-Path $cartellaStrum "esclusi-personali.txt" }
$registro = Join-Path $cartellaStrum "registro-corse.log"

foreach ($p in @($cartellaSorgenti, $Esclusi)) {
  if (-not (Test-Path -LiteralPath $p)) { throw "Non trovato: $p" }
}
if (-not $SoloPiano -and -not (Get-Command $Transcribe -ErrorAction SilentlyContinue)) { throw "Comando non trovato: $Transcribe" }
if ($CancellaVideo -and -not $Sovrascrittura) {
  throw "Con -CancellaVideo devi scegliere come rimuovere: -Sovrascrittura si (riscrive i byte prima di rimuovere) oppure -Sovrascrittura no (rimozione normale). La scelta si fa adesso, non a corsa avviata."
}
if ($CancellaVideo -and $Sovrascrittura -eq "si") {
  if (-not (Get-Command $Python -ErrorAction SilentlyContinue)) { throw "Comando non trovato: $Python" }
  if (-not (Test-Path -LiteralPath $Sovrascrivi)) { throw "Non trovato: $Sovrascrivi" }
}
New-Item -ItemType Directory -Force -Path $cartellaStrum | Out-Null

$schemi = Get-Content -LiteralPath $Esclusi -Encoding UTF8 |
          Where-Object { $_.Trim() -and -not $_.TrimStart().StartsWith("#") } |
          ForEach-Object { $_.Trim() }

function Get-DurataSecondi([string]$percorso) {
  if (-not (Test-Path -LiteralPath $Ffprobe)) { return -1 }
  $out = & $Ffprobe -v error -show_entries format=duration -of csv=p=0 $percorso 2>$null
  if ($LASTEXITCODE -ne 0 -or -not $out) { return -1 }
  # ffprobe scrive il separatore decimale con il punto. In locale italiano il punto e'
  # il separatore delle migliaia, quindi "300.012000" verrebbe letto come 300012000 e la
  # copertura risulterebbe dello zero per cento: si impone la cultura invariante.
  $val = 0.0
  $testo = ($out | Select-Object -First 1).Trim()
  $stile = [Globalization.NumberStyles]::Float
  $cultura = [Globalization.CultureInfo]::InvariantCulture
  if ([double]::TryParse($testo, $stile, $cultura, [ref]$val)) { return $val }
  return -1
}

function Get-FineSrtSecondi([string]$percorso) {
  if (-not (Test-Path -LiteralPath $percorso)) { return -1 }
  $ultima = Select-String -LiteralPath $percorso -Pattern '-->' | Select-Object -Last 1
  if (-not $ultima) { return -1 }
  $m = [regex]::Match($ultima.Line, '-->\s*(\d+):(\d+):(\d+)[,.](\d+)')
  if (-not $m.Success) { return -1 }
  return [double]$m.Groups[1].Value * 3600 + [double]$m.Groups[2].Value * 60 + [double]$m.Groups[3].Value
}

function Test-TrascrizioneCompleta($video, [string]$txt, [string]$srt) {
  # Quattro condizioni, tutte necessarie: il testo esiste e non e' un moncone,
  # i sottotitoli esistono, e l'ultimo sottotitolo copre quasi tutta la durata del video.
  # Senza la durata del video non si dichiara completa: nel dubbio si conserva.
  if (-not (Test-Path -LiteralPath $txt)) { return @{ ok = $false; perche = "manca il .txt" } }
  if ((Get-Item -LiteralPath $txt).Length -lt 1000) { return @{ ok = $false; perche = "il .txt e' troppo corto" } }
  if (-not (Test-Path -LiteralPath $srt)) { return @{ ok = $false; perche = "manca il .srt" } }
  $durata = Get-DurataSecondi $video.FullName
  if ($durata -le 0) { return @{ ok = $false; perche = "durata del video non leggibile" } }
  $fine = Get-FineSrtSecondi $srt
  if ($fine -le 0) { return @{ ok = $false; perche = "ultimo sottotitolo non leggibile" } }
  $copertura = $fine / $durata
  if ($copertura -lt $SogliaCopertura) {
    return @{ ok = $false; perche = ("copertura {0:P1} sotto la soglia {1:P0}" -f $copertura, $SogliaCopertura) }
  }
  return @{ ok = $true; perche = ("copertura {0:P1}" -f $copertura) }
}

function Get-NomeUscita([string]$titolo) {
  # Replica _sanitize di src/transcriptor/sources/local.py: caratteri vietati -> _, taglio a 120.
  $pulito = ($titolo.ToCharArray() | ForEach-Object { if ('<>:"/\|?*'.Contains($_)) { '_' } else { $_ } }) -join ''
  $pulito = $pulito.Trim()
  if ($pulito.Length -gt 120) { $pulito = $pulito.Substring(0, 120) }
  if (-not $pulito) { $pulito = "transcript" }
  return $pulito
}

$file = Get-ChildItem -LiteralPath $cartellaSorgenti -Recurse -File |
        Where-Object { $estensioni -contains $_.Extension.ToLower() } |
        Sort-Object FullName

$daFare = @(); $esclusiN = 0; $giaFatti = 0; $daRifare = 0
foreach ($f in $file) {
  $colpito = $false
  foreach ($s in $schemi) { if ($f.FullName -imatch $s) { $colpito = $true; break } }
  if ($colpito) { $esclusiN++; continue }

  $relDir = $f.DirectoryName.Substring($cartellaSorgenti.Length).TrimStart('\', '/')
  $destDir = if ($relDir) { Join-Path $cartellaUscita $relDir } else { $cartellaUscita }
  $atteso = Join-Path $destDir ((Get-NomeUscita $f.BaseName) + ".txt")
  $perche = ""
  if (Test-Path -LiteralPath $atteso) {
    # Non basta che il file esista: una corsa interrotta a meta' scrittura, per esempio
    # perche' il disco e' stato staccato, lascia un testo monco che sembra lavoro finito.
    $verificaPrec = Test-TrascrizioneCompleta $f $atteso ([IO.Path]::ChangeExtension($atteso, ".srt"))
    if ($verificaPrec.ok) { $giaFatti++; continue }
    $perche = "da rifare: " + $verificaPrec.perche
    $daRifare++
  }
  $daFare += [pscustomobject]@{ File = $f; Dest = $destDir; Atteso = $atteso; Perche = $perche }
}

if ($Quanti -gt 0 -and $daFare.Count -gt $Quanti) { $daFare = $daFare[0..($Quanti - 1)] }

Write-Host ""
Write-Host "Trascrizione di $Radice - modello $Modello, lingua $Lingua, vad $Vad, formati $Formati"
if ($CancellaVideo) { Write-Host "  cancellazione video ATTIVA ($(if ($Sovrascrittura -eq 'si') { 'con sovrascrittura dei byte' } else { 'rimozione normale' })): solo dopo verifica di copertura >= $([int]($SogliaCopertura*100))%" } else { Write-Host "  cancellazione video: disattivata" }
Write-Host ("  registrazioni trovate : {0}" -f $file.Count)
Write-Host ("  escluse (personali)   : {0}" -f $esclusiN)
Write-Host ("  gia' trascritte       : {0}" -f $giaFatti)
Write-Host ("  da rifare (incomplete): {0}" -f $daRifare)
Write-Host ("  da trascrivere ora    : {0}" -f $daFare.Count)
Write-Host ""

if ($SoloPiano) {
  foreach ($v in $daFare) { Write-Host ("  [ ] " + $v.File.Name + $(if ($v.Perche) { "   <- " + $v.Perche } else { "" })) }
  Write-Host ""
  Write-Host "Solo piano: non e' stato eseguito nulla."
  return
}

$inizio = Get-Date; $ok = 0; $ko = 0; $i = 0; $rimossi = 0; $incomplete = 0; $interrotto = $false
foreach ($v in $daFare) {
  $i++
  if (-not (Test-Path -LiteralPath $cartellaSorgenti)) {
    Write-Host ""
    Write-Host "Il disco non risponde piu': la cartella delle registrazioni non c'e'."
    $interrotto = $true
    break
  }
  New-Item -ItemType Directory -Force -Path $v.Dest | Out-Null
  Write-Host ("[{0}/{1}] {2}" -f $i, $daFare.Count, $v.File.Name)
  $t0 = Get-Date
  & $Transcribe file $v.File.FullName --language $Lingua --model $Modello --vad $Vad --formats $Formati --out $v.Dest
  $esito = if ($LASTEXITCODE -eq 0 -and (Test-Path -LiteralPath $v.Atteso)) { "ok" } else { "FALLITO" }
  $durata = [int]((Get-Date) - $t0).TotalSeconds
  if ($esito -eq "ok") { $ok++ } else { $ko++ }
  $nota = ""
  if ($esito -eq "ok") {
    $srt = [IO.Path]::ChangeExtension($v.Atteso, ".srt")
    $verifica = Test-TrascrizioneCompleta $v.File $v.Atteso $srt
    if ($verifica.ok) {
      $nota = "completa, " + $verifica.perche
      if ($CancellaVideo) {
        if ($Sovrascrittura -eq "si") {
          & $Python $Sovrascrivi --radice $Radice --si $v.File.FullName | Out-Null
          $come = "sovrascritto e rimosso"
        } else {
          Remove-Item -LiteralPath $v.File.FullName -Force
          $come = "rimosso"
        }
        if (Test-Path -LiteralPath $v.File.FullName) { $nota += "; VIDEO NON RIMOSSO" }
        else { $nota += "; video $come"; $rimossi++ }
      }
    } else {
      $nota = "INCOMPLETA: " + $verifica.perche + "; video conservato"
      $incomplete++
    }
  }
  $riga = "{0}`t{1}`t{2}+{3}`t{4}s`t{5}`t{6}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $esito, $Modello, $Vad, $durata, $v.File.Name, $nota
  try { Add-Content -LiteralPath $registro -Value $riga -Encoding UTF8 -ErrorAction Stop }
  catch { Write-Host "    (registro non scrivibile: il disco potrebbe essere stato staccato)" }
  Write-Host ("    {0} in {1}s  {2}" -f $esito, $durata, $nota)
}

$tot = [int]((Get-Date) - $inizio).TotalMinutes
Write-Host ""
Write-Host ("Fatto: {0} trascritte, {1} fallite, {2} saltate perche' gia' presenti, {3} escluse perche' personali. Tempo totale {4} min." -f $ok, $ko, $giaFatti, $esclusiN, $tot)
Write-Host ("Video: {0} rimossi dopo verifica, {1} conservati perche' la trascrizione non copriva tutta la durata." -f $rimossi, $incomplete)
if ($interrotto -or $daFare.Count -gt $i) {
  Write-Host ""
  Write-Host "CORSA INTERROTTA. Rilancia lo stesso comando quando il disco e' ricollegato:"
  Write-Host "  riprende da dove si era fermata, e rifa' da capo l'eventuale lezione lasciata a meta'."
}
Write-Host ("Registro: {0}" -f $registro)
