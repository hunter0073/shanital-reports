#!/usr/bin/env python3
"""
Shani Tal Marketing - Service Report Server
Run:  python3 server.py
Then: open app.html on any phone on the same WiFi network
"""
from flask import Flask, request, jsonify, send_file
import subprocess, tempfile, os, base64, json, re
from datetime import datetime

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shantal_logo.png')
with open(LOGO_PATH, 'rb') as f:
    LOGO_B64 = base64.b64encode(f.read()).decode()

def h(s):
    if not s: return ''
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

def v(d, k, default=''):
    val = d.get(k, default)
    return str(val).strip() if val else default

def make_full_html(d):
    warr = ''
    if v(d,'warrFrom') and v(d,'warrTo'):
        warr = v(d,'warrFrom') + ' עד ' + v(d,'warrTo')
    elif v(d,'warrFrom'):
        warr = v(d,'warrFrom')

    sig_eng_html  = f'<img src="{v(d,"sigEng")}"  style="max-height:20px;max-width:70px;vertical-align:middle;"/>' if d.get('sigEng')  else ''
    sig_cust_html = f'<img src="{v(d,"sigCust")}" style="max-height:20px;max-width:70px;vertical-align:middle;"/>' if d.get('sigCust') else ''

    info_rows = f"""
    <tr>
      <td class="lbl">:&#1500;&#1499;&#1489;&#1493;&#1491;</td><td class="val">{h(v(d,'customer'))}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1499;&#1514;&#1493;&#1489;&#1514;</td><td class="val">{h(v(d,'address'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1514;&#1497;&#1488;&#1493;&#1512; &#1492;&#1496;&#1497;&#1508;&#1493;&#1500;</td><td class="val">{h(v(d,'problemType') or v(d,'fault')[:40])}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1506;&#1497;&#1512;</td><td class="val">{h(v(d,'city'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1505;&#1496;&#1496;&#1493;&#1505;</td><td class="val">{h(v(d,'status'))}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1502;&#1497;&#1511;&#1493;&#1501;</td><td class="val">{h(v(d,'location'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1488;&#1495;&#1512;&#1497;&#1493;&#1514;</td><td class="val">{h(warr)}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1488;&#1497;&#1513; &#1511;&#1513;&#1512;</td><td class="val">{h(v(d,'contact'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1514;&#1488;&#1512;&#1497;&#1498; &#1492;&#1490;&#1506;&#1492;</td>
      <td class="val">{h(v(d,'date'))} &nbsp;<span style="color:#555">:&#1513;&#1506;&#1514; &#1492;&#1490;&#1506;&#1492;</span>&nbsp; {h(v(d,'time'))}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1502;&#1505;' &#1496;&#1500;&#1508;&#1493;&#1503;</td><td class="val">{h(v(d,'phone'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1502;&#1505;' &#1492;&#1494;&#1502;&#1504;&#1514; &#1500;&#1511;&#1493;&#1495;</td><td class="val">{h(v(d,'custOrder'))}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1496;&#1500;&#1508;&#1493;&#1503; &#1504;&#1497;&#1497;&#1491;</td><td class="val">{h(v(d,'mobile'))}</td>
    </tr>
    <tr>
      <td class="lbl dev-sep">:&#1514;&#1497;&#1488;&#1493;&#1512;</td><td class="val dev-sep">{h(v(d,'deviceDesc'))}</td>
      <td class="mid dev-sep"></td>
      <td class="lbl dev-sep">:&#1514;&#1488;&#1512;&#1497;&#1498; &#1492;&#1514;&#1511;&#1504;&#1492;</td><td class="val dev-sep">{h(v(d,'installDate'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1511;&#1493;&#1491; &#1508;&#1512;&#1497;&#1496;</td><td class="val">{h(v(d,'itemCode'))}</td>
      <td class="mid"></td>
      <td class="lbl">:&#1492;&#1506;&#1512;&#1493;&#1514;</td><td class="val">{h(v(d,'deviceNotes'))}</td>
    </tr>
    <tr>
      <td class="lbl">:&#1502;&#1505;"&#1491;</td><td class="val">{h(v(d,'serial'))}</td>
      <td class="mid"></td><td></td><td></td>
    </tr>"""

    parts = d.get('parts', [])
    parts_html = ''
    if parts:
        rows = ''.join(f'<tr><td>{h(p.get("code",""))}</td><td>{h(p.get("desc",""))}</td><td style="text-align:center;">{h(p.get("qty","1"))}</td></tr>' for p in parts)
        parts_html = f'<table class="parts-tbl"><tr><th>&#1511;&#1493;&#1491; &#1508;&#1512;&#1497;&#1496;</th><th>&#1514;&#1497;&#1488;&#1493;&#1512;</th><th>&#1499;&#1502;&#1493;&#1514;</th></tr>{rows}</table>'

    photos_html = ''
    if d.get('photos'):
        photos_html = '<div style="margin-top:5mm;"><div class="p2-lbl">:&#1514;&#1502;&#1493;&#1504;&#1493;&#1514;</div><div style="display:flex;flex-wrap:wrap;gap:3mm;">'
        for p in d['photos'][:6]:
            photos_html += f'<img src="{p}" style="width:52mm;height:40mm;object-fit:cover;border:0.5px solid #ccc;"/>'
        photos_html += '</div></div>'

    travel_dist = (v(d,'travelDist') + ' &#1511;"&#1502;') if v(d,'travelDist') else ''
    parking_val = ('&#8362;' + v(d,'parking')) if v(d,'parking') else ''
    intExt = h(v(d,'intExt','&#1495;&#1493;&#1509;'))
    callNum = h(v(d,'callNum',''))
    engineer = h(v(d,'engineer'))
    date = h(v(d,'date'))
    time_ = h(v(d,'time'))

    hdr = f"""
    <div class="logo-row"><img src="data:image/png;base64,{LOGO_B64}"/></div>
    <div class="hdr-flex">
      <div class="hdr-left">
        <span class="k">:&#1514;&#1488;&#1512;&#1497;&#1498;</span> {date}<br/>
        <span class="k">:&#1513;&#1506;&#1492;</span> {time_}<br/>
        <span class="k">:&#1496;&#1499;&#1504;&#1488;&#1497;</span> {engineer}
      </div>
      <div class="report-title">&#1491;&#1493;"&#1495; &#1513;&#1497;&#1512;&#1493;&#1514; - {intExt} &nbsp; {callNum}</div>
    </div>
    <table class="info-table">{info_rows}</table>"""

    footer = """
    <div class="footer">
      <div>&#1499;&#1514;&#1493;&#1489;&#1514;: &#1488;&#1497;&#1502;&#1489;&#1512; 7, &#1511;&#1512;&#1497;&#1497;&#1514; &#1488;&#1512;&#1497;&#1492;, &#1514;.&#1491; 10359, &#1508;&#1514;&#1495; &#1514;&#1511;&#1493;&#1493;&#1492; 4900302 &nbsp;|&nbsp; &#1496;&#1500;&#1508;&#1493;&#1503;: 03-9314177 &nbsp;|&nbsp; &#1508;&#1511;&#1505;: 03-9314188</div>
      <div style="direction:ltr;">Address: 7 Imber st. Kiryat Arye, P.O.B 10359, Petah Tikva 4900302 | Tel: +972 3 9314177 | Fax: +972 3 9314188</div>
    </div>"""

    css = """
    * { margin:0; padding:0; box-sizing:border-box; }
    body { font-family: Arial, "Arial Hebrew", Helvetica, sans-serif; font-size:9pt; direction:rtl; color:#000; }
    .page { width:210mm; min-height:297mm; padding:6mm 12mm 20mm 12mm; position:relative; page-break-after:always; }
    .page:last-child { page-break-after:avoid; }
    .logo-row { text-align:center; margin-bottom:3mm; }
    .logo-row img { height:14mm; }
    .hdr-flex { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:2mm; }
    .hdr-left { font-size:8.5pt; line-height:1.9; }
    .hdr-left .k { color:#555; }
    .report-title { font-size:15pt; font-weight:bold; text-align:center; flex:1; padding-top:1mm; }
    .info-table { width:100%; border-collapse:collapse; border:1.2px solid #000; margin-bottom:3mm; font-size:8.5pt; }
    .info-table td { padding:2.5px 5px; vertical-align:middle; }
    .info-table .lbl { color:#333; white-space:nowrap; text-align:right; width:28mm; }
    .info-table .val { text-align:right; }
    .info-table .mid { width:1px; padding:0; background:#000; }
    .info-table .dev-sep { border-top:1.2px solid #000; }
    .work-box { border:1.2px solid #000; margin-bottom:3mm; }
    .work-title { text-align:center; font-size:11pt; font-weight:bold; text-decoration:underline; padding:3px 5px; border-bottom:1px solid #ccc; }
    .wl { border-bottom:0.4px solid #bbb; min-height:8mm; padding:1.5px 4px; text-align:right; font-size:8.5pt; }
    .btm { width:100%; font-size:8.5pt; border-collapse:collapse; }
    .btm td { padding:2.5px 4px; vertical-align:bottom; }
    .btm .k { text-align:right; white-space:nowrap; }
    .fl { border-bottom:0.6px solid #000; display:inline-block; min-height:5mm; text-align:right; padding:0 2px; vertical-align:bottom; }
    .p2-lbl { font-size:9pt; font-weight:bold; margin-bottom:1mm; text-align:right; color:#1B2F5E; }
    .p2-wl { border-bottom:0.4px solid #bbb; min-height:7mm; padding:1.5px 3px; text-align:right; font-size:8.5pt; margin-bottom:1px; }
    .stbl { width:100%; border-collapse:collapse; font-size:8.5pt; margin-top:2mm; }
    .stbl .sl { text-align:right; white-space:nowrap; padding:2px 5px; }
    .stbl .sv { border-bottom:0.6px solid #000; min-width:28mm; padding:0 3px 1px; }
    .parts-tbl { width:100%; border-collapse:collapse; font-size:8pt; margin-top:3mm; border:0.5px solid #ccc; }
    .parts-tbl th { background:#EBF0FA; border:0.5px solid #ccc; padding:3px 6px; text-align:right; font-weight:bold; color:#1B2F5E; }
    .parts-tbl td { border:0.5px solid #ccc; padding:3px 6px; text-align:right; }
    .footer { position:absolute; bottom:5mm; left:12mm; right:12mm; border-top:0.7px solid #000; padding-top:2mm; text-align:center; font-size:7pt; color:#333; }
    @page { size:A4; margin:0; }
    """

    fault = h(v(d,'fault'))
    solution = h(v(d,'solution'))
    timeOut = h(v(d,'timeOut'))
    timeReturn = h(v(d,'timeReturn'))
    travelTime = h(v(d,'travelTime'))
    workDate = h(v(d,'workDate'))
    workStart = h(v(d,'workStart'))
    workEnd = h(v(d,'workEnd'))
    custSigner = h(v(d,'custSignerName'))
    problemType = h(v(d,'problemType'))
    callType = h(v(d,'callType'))
    actualHours = h(v(d,'actualHours'))

    page1_content = f"""
    <div class="work-box">
      <div class="work-title">&#1514;&#1488;&#1493;&#1512; &#1492;&#1496;&#1497;&#1508;&#1493;&#1500; / &#1502;&#1492;&#1493;&#1514; &#1492;&#1506;&#1489;&#1493;&#1491;&#1492;</div>
      <div class="wl">{fault}</div>
      <div class="wl">&nbsp;</div>
      <div class="wl">{solution}</div>
      <div class="wl">&nbsp;</div>
      <div class="wl">&nbsp;</div>
      <div class="wl">&nbsp;</div>
      <div style="display:flex;justify-content:space-between;border-top:0.4px solid #bbb;padding:2px 4px;min-height:8mm;">
        <span class="fl" style="min-width:55mm;">&nbsp;</span>
        <span class="fl" style="min-width:70mm;">&nbsp;</span>
      </div>
    </div>
    <table class="btm">
      <tr>
        <td class="k">:&#1513;&#1506;&#1514; &#1497;&#1510;&#1497;&#1488;&#1492;</td>
        <td><span class="fl" style="min-width:32mm;">{timeOut}</span></td>
        <td class="k">:&#1494;&#1502;&#1503; &#1504;&#1505;&#1497;&#1506;&#1492;</td>
        <td><span class="fl" style="min-width:28mm;">{travelTime}</span></td>
      </tr>
      <tr>
        <td class="k">:&#1513;&#1506;&#1514; &#1495;&#1494;&#1512;&#1492;</td>
        <td><span class="fl" style="min-width:32mm;">{timeReturn}</span></td>
        <td class="k">:&#1502;&#1512;&#1495;&#1511; &#1504;&#1505;&#1497;&#1506;&#1492;</td>
        <td><span class="fl" style="min-width:28mm;">{travel_dist}</span></td>
      </tr>
      <tr>
        <td class="k">:&#1496;&#1499;&#1504;&#1488;&#1497;</td>
        <td colspan="3"><span class="fl" style="min-width:65mm;">{engineer}</span></td>
      </tr>
      <tr>
        <td class="k">:&#1514;&#1488;&#1512;&#1497;&#1498; &#1489;&#1497;&#1510;&#1493;&#1506;</td>
        <td><span class="fl" style="min-width:32mm;">{workDate}</span></td>
        <td></td><td></td>
      </tr>
      <tr>
        <td class="k">:&#1513;&#1506;&#1514; &#1492;&#1514;&#1495;&#1500;&#1492;</td>
        <td><span class="fl" style="min-width:32mm;">{workStart}</span></td>
        <td></td><td></td>
      </tr>
      <tr>
        <td class="k">:&#1513;&#1506;&#1514; &#1505;&#1497;&#1493;&#1501;</td>
        <td><span class="fl" style="min-width:32mm;">{workEnd}</span></td>
        <td class="k">:&#1495;&#1514;&#1497;&#1502;&#1514; &#1496;&#1499;&#1504;&#1488;&#1497;</td>
        <td><span class="fl" style="min-width:50mm;">{sig_eng_html}</span></td>
      </tr>
      <tr>
        <td class="k">:&#1513;&#1501; &#1500;&#1511;&#1493;&#1495;</td>
        <td colspan="3"><span class="fl" style="min-width:65mm;">{custSigner}</span></td>
      </tr>
      <tr>
        <td colspan="2">
          <div style="text-align:right;">:&#1505;&#1493;&#1490; &#1489;&#1506;&#1497;&#1492; &nbsp; {problemType}</div>
          <div style="text-align:right;margin-top:2px;">:&#1505;&#1493;&#1490; &#1511;&#1512;&#1497;&#1488;&#1492; &nbsp; {callType}</div>
        </td>
        <td colspan="2" style="vertical-align:bottom;">
          <span class="fl" style="min-width:50mm;">{sig_cust_html}</span>
        </td>
      </tr>
    </table>
    <div style="font-size:11pt;font-weight:bold;margin-top:3mm;">{intExt}</div>"""

    page2_content = f"""
    <div style="margin-bottom:3mm;">
      <div class="p2-lbl">:&#1514;&#1511;&#1500;&#1492;</div>
      <div class="p2-wl">{fault}</div>
      <div class="p2-wl">&nbsp;</div>
      <div class="p2-wl">&nbsp;</div>
    </div>
    <div style="margin-bottom:3mm;">
      <div class="p2-lbl">:&#1508;&#1514;&#1512;&#1493;&#1503;</div>
      <div class="p2-wl">{solution}</div>
      <div class="p2-wl">&nbsp;</div>
      <div class="p2-wl">&nbsp;</div>
    </div>
    <table class="stbl">
      <tr><td class="sl">:&#1513;&#1506;&#1493;&#1514; &#1506;&#1489;&#1493;&#1491;&#1492; &#1489;&#1508;&#1493;&#1506;&#1500;</td><td class="sv">{actualHours}</td><td style="width:15mm;"></td><td></td></tr>
      <tr><td class="sl">:&#1494;&#1502;&#1503; &#1504;&#1505;&#1497;&#1506;&#1492; &#1489;&#1508;&#1493;&#1506;&#1500;</td><td class="sv">{travelTime}</td><td></td><td></td></tr>
      <tr><td class="sl">:&#1502;&#1512;&#1495;&#1511; &#1504;&#1505;&#1497;&#1506;&#1492; &#1489;&#1508;&#1493;&#1506;&#1500;</td><td class="sv">{travel_dist}</td><td></td><td></td></tr>
      <tr><td class="sl">:&#1506;&#1500;&#1493;&#1514; &#1495;&#1504;&#1497;&#1497;&#1492;</td><td class="sv">{parking_val}</td><td></td><td></td></tr>
    </table>
    {parts_html}
    {photos_html}"""

    return f"""<!DOCTYPE html>
<html lang="he" dir="rtl">
<head><meta charset="UTF-8"/><style>{css}</style></head>
<body>
<div class="page">{hdr}{page1_content}{footer}</div>
<div class="page">{hdr}{page2_content}{footer}</div>
</body></html>"""


def build_pdf(data):
    html = make_full_html(data)
    with tempfile.NamedTemporaryFile(suffix='.html', delete=False, mode='w', encoding='utf-8') as f:
        f.write(html)
        tmp = f.name
    pdf = tmp.replace('.html', '.pdf')
    result = subprocess.run([
        'wkhtmltopdf',
        '--encoding', 'utf-8',
        '--page-size', 'A4',
        '--margin-top', '0', '--margin-bottom', '0',
        '--margin-left', '0', '--margin-right', '0',
        '--disable-smart-shrinking',
        '--enable-local-file-access',
        '--quiet',
        tmp, pdf
    ], capture_output=True, text=True, timeout=30)
    os.unlink(tmp)
    if result.returncode != 0 or not os.path.exists(pdf):
        raise Exception(result.stderr or 'PDF generation failed')
    return pdf


@app.route('/generate_pdf', methods=['POST', 'OPTIONS'])
def generate_pdf():
    if request.method == 'OPTIONS':
        return '', 200
    try:
        data = request.get_json(force=True)
        pdf_path = build_pdf(data)
        cust = re.sub(r'[^\w]', '_', data.get('customer', 'report'))[:25]
        filename = f"Service_Report_{data.get('callNum','---')}_{cust}.pdf"
        return send_file(pdf_path, mimetype='application/pdf', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    return send_file('app.html')

@app.route('/health')
def health():
    return jsonify({'ok': True, 'time': datetime.now().isoformat()})


@app.after_request
def cors(r):
    r.headers['Access-Control-Allow-Origin'] = '*'
    r.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    r.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return r


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    print('\n' + '='*50)
    print('  Shani Tal - Service Report Server')
    print(f'  Running on port {port}')
    print('='*50 + '\n')
    app.run(host='0.0.0.0', port=port, debug=False)
