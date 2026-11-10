/**
 * BLOOM by Jana — automatische bevestigingsmail + overzicht van aanvragen in Google Sheets.
 * Plak deze code in je Google Apps Script (vervang de oude code) en implementeer als webapp.
 */
var VAN_NAAM = 'BLOOM by Jana';
var ANTWOORD_NAAR = 'Bloom_byjana@outlook.com';   // antwoorden van klanten komen hier terecht
var MAX_PER_DAG = 80;                              // vangnet tegen misbruik
var TIJDZONE = 'Europe/Brussels';

// Pas gerust de teksten aan.
var TEKSTEN = {
  frame: {
    onderwerp: 'Bedankt voor je aanvraag voor The Bloom Frame',
    tekst: 'Wat fijn dat jullie jullie boeket bij mij willen laten bewaren! Ik heb jullie aanvraag goed ontvangen en bevestig jullie trouwdatum zo snel mogelijk persoonlijk. Jullie datum is pas definitief nadat je mijn bevestiging hebt ontvangen. Het voorschot bedraagt €150; ik laat je weten hoe en wanneer je dat kunt betalen.'
  },
  bar: {
    onderwerp: 'Bedankt voor je aanvraag voor The Bloom Bar',
    tekst: 'Wat leuk dat jullie aan een Bloom Bar denken! Ik bekijk jullie datum, locatie, aantal gasten en wensen en maak daarna persoonlijk een voorstel.'
  },
  florals: {
    onderwerp: 'Bedankt voor je aanvraag voor The Bloom Florals',
    tekst: 'Bedankt voor jullie bericht! Ik bekijk jullie trouwdatum, locatie en bloemenwensen en neem snel contact op voor een kennismaking.'
  },
  contact: {
    onderwerp: 'Bedankt voor je bericht aan BLOOM by Jana',
    tekst: 'Bedankt voor je bericht! Ik lees alles rustig na en neem zo snel mogelijk contact met je op.'
  }
};

function doPost(e) {
  try {
    var d = JSON.parse(e.postData.contents);
    var mail = String(d.email || '').trim();
    if (d._gotcha || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(mail)) return antwoord_();
    var cache = CacheService.getScriptCache();
    var sleutel = 'mail:' + mail.toLowerCase();
    if (cache.get(sleutel)) return antwoord_();          // max. 1 mail per adres per 10 minuten
    cache.put(sleutel, '1', 600);
    var props = PropertiesService.getScriptProperties();
    var dag = Utilities.formatDate(new Date(), TIJDZONE, 'yyyy-MM-dd');
    var n = parseInt(props.getProperty('dag:' + dag) || '0', 10);
    if (n >= MAX_PER_DAG) return antwoord_();
    props.setProperty('dag:' + dag, String(n + 1));
    noteer_(d);
    stuurBevestiging_(d, mail);
  } catch (err) {
    console.error(err);
  }
  return antwoord_();
}

function doGet() {
  return ContentService.createTextOutput('[]').setMimeType(ContentService.MimeType.JSON);
}

function antwoord_() {
  return ContentService.createTextOutput('ok');
}

function voornaam_(d) {
  return d['Voornaam'] || String(d['Voornaam en achternaam'] || '').split(' ')[0] || '';
}

function details_(d) {
  var overslaan = { email: 1, dienst: 1, pagina: 1 };
  return Object.keys(d).filter(function (k) {
    return k.charAt(0) !== '_' && !overslaan[k] && d[k];
  }).map(function (k) { return [k, String(d[k])]; });
}

function noteer_(d) {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  if (!ss) return;                                       // script staat los van een Sheet: overslaan
  var blad = ss.getSheetByName('Aanvragen') || ss.insertSheet('Aanvragen');
  if (blad.getLastRow() === 0) blad.appendRow(['Ontvangen', 'Dienst', 'Naam', 'E-mail', 'Details']);
  var naam = [d['Voornaam'], d['Achternaam']].filter(Boolean).join(' ') || d['Voornaam en achternaam'] || '';
  var regels = details_(d).map(function (r) { return r[0] + ': ' + r[1]; }).join('\n');
  blad.appendRow([new Date(), d.dienst || '', naam, d.email || '', regels]);
}

function esc_(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function stuurBevestiging_(d, mail) {
  var dienst = String(d.dienst || '').toLowerCase();
  var t = TEKSTEN[dienst.indexOf('frame') > -1 ? 'frame' : dienst.indexOf('bar') > -1 ? 'bar' : dienst.indexOf('florals') > -1 ? 'florals' : 'contact'];
  var rijen = details_(d);
  var groet = 'Hi' + (voornaam_(d) ? ' ' + voornaam_(d) : '') + ',';
  var plat = groet + '\n\n' + t.tekst + '\n\nDit heb ik van jullie ontvangen:\n' +
    rijen.map(function (r) { return '- ' + r[0] + ': ' + r[1]; }).join('\n') +
    '\n\nLots of love,\nJana ♡\nBLOOM by Jana';
  var html = '<div style="font-family:Arial,sans-serif;color:#4A3F3A;line-height:1.6;max-width:560px">' +
    '<p>' + esc_(groet) + '</p><p>' + esc_(t.tekst) + '</p><p><strong>Dit heb ik van jullie ontvangen:</strong></p><ul>' +
    rijen.map(function (r) { return '<li>' + esc_(r[0]) + ': ' + esc_(r[1]) + '</li>'; }).join('') +
    '</ul><p>Lots of love,<br>Jana ♡<br>BLOOM by Jana</p></div>';
  MailApp.sendEmail({ to: mail, subject: t.onderwerp, body: plat, htmlBody: html, name: VAN_NAAM, replyTo: ANTWOORD_NAAR });
}

// Voer deze functie één keer uit (▶) om toestemming te geven en een testmail naar jezelf te sturen.
function test() {
  var d = { Voornaam: 'Test', Achternaam: 'Klant', email: ANTWOORD_NAAR, dienst: 'The Bloom Frame', Trouwdatum: '2027-06-12', 'Type frame': 'A4 vlak — €215', 'Dubbelzijdig glas': 'Ja' };
  noteer_(d);
  stuurBevestiging_(d, ANTWOORD_NAAR);
}
