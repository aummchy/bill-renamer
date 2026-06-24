import re
import dateparser

INVOICE_KW = ["invoice no", "invoice number"]
BILL_KW = ["bill", "bill no"]

def _has_kw(text_lower: str, kw: str) -> bool:
    if " " in kw:
        return kw in text_lower
    return bool(re.search(r'\b' + re.escape(kw) + r'\b', text_lower))

def _extract_near(texts, keywords, kw_compact_list):
    for i, text in enumerate(texts):
        text_compact = text.lower().replace(" ", "").replace("\u00a0", "")
        for compact in kw_compact_list:
            if compact in text_compact:
                remainder = re.sub(r'(?i)(?:invoice|inv|bill)\s*no', '', text).strip().lstrip(":\uff1a.").strip()
                remainder = re.sub(r'^[^A-Za-z0-9\-/]+', '', remainder)
                if remainder and re.match(r'^[A-Za-z0-9\-/]+$', remainder) and len(remainder) > 1:
                    return remainder
                for j in range(1, 4):
                    if i + j < len(texts):
                        nxt = texts[i + j].strip().lstrip(":\uff1a").strip()
                        if not nxt:
                            continue
                        if re.match(r'^[A-Za-z0-9\-/]+$', nxt) and len(nxt) > 1 and any(c.isdigit() for c in nxt):
                            return nxt
                        break
    for i, text in enumerate(texts):
        text_lower = text.lower().strip()
        for kw in keywords:
            if _has_kw(text_lower, kw):
                for j in range(0, 4):
                    if i + j < len(texts):
                        candidate = texts[i + j].strip().lstrip(":\uff1a").strip()
                        match = re.match(r'^[A-Za-z0-9\-/]+$', candidate)
                        if match and len(candidate) > 1 and any(c.isdigit() for c in candidate) and candidate.lower() not in (k.replace(" ", "") for k in keywords):
                            return candidate
                        if j > 0 and candidate:
                            break
    return None

def extract_invoice_number(texts: list[str]) -> str:
    invoice_compact = ["invoiceno"]
    bill_compact = ["billno"]
    result = _extract_near(texts, INVOICE_KW, invoice_compact)
    if result:
        return result
    result = _extract_near(texts, BILL_KW, bill_compact)
    if result:
        return result
    for text in texts:
        text_clean = text.strip().lstrip(":\uff1a").strip()
        if re.match(r'^\d{3,}$', text_clean):
            return text_clean
    return "UnknownInvoice"

def extract_date(texts: list[str]) -> str:
    all_text = " ".join(texts)
    date_formats = [
        (r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b', "DMY"),
        (r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b', "DMY"),
        (r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', "YMD"),
    ]
    for pattern, fmt in date_formats:
        matches = re.findall(pattern, all_text)
        for m in matches:
            if fmt == "DMY":
                day, month, year = m
            elif fmt == "YMD":
                year, month, day = m
            else:
                continue
            try:
                d, mo, y = int(day), int(month), int(year)
                if y < 100:
                    y += 2000
                if 1 <= mo <= 12 and 1 <= d <= 31 and 2000 <= y <= 2099:
                    return f"{day.zfill(2)}-{month.zfill(2)}-{y}"
            except ValueError:
                continue
    for text in texts:
        parsed = dateparser.parse(text, settings={'PREFER_DAY_OF_MONTH': 'first'})
        if parsed and 2000 <= parsed.year <= 2099:
            return parsed.strftime("%d-%m-%Y")
    return "UnknownDate"

def extract_name(texts: list[str], boxes: list, name_filters: dict | None = None,
                 img_width: int = 0, img_height: int = 0) -> str:
    if not boxes or not texts:
        return "UnknownName"
    max_len = (name_filters or {}).get("max_length", 30)
    max_commas = (name_filters or {}).get("max_commas", 2)
    max_nums = (name_filters or {}).get("max_numbers", 2)
    skip_words = (name_filters or {}).get("skip_words", [])

    if img_height <= 0:
        img_height = max(max(pt[1] for pt in box) for box in boxes) if boxes else 1

    top_quarter = img_height / 4

    skip_pattern = re.compile(
        r'\binvoice\b|\bbill\b|\beway\b|\back\b|\birn\b'
        r'|\bstate\b|\bcode\b|\bgst\b|\bpan\b|\bsac\b'
        r'|\bdate\b|\bdated\b|\bref\b|\bno\b|\bnumber\b'
        r'|\baddress\b|\bship\s*to\b|\bship\s*from\b'
        r'|\bbuyer\b|\bconsignee\b|\bdispatch\b'
        r'|\bphone\b|\bemail\b|\bwww\b|\bcom\b|\bin\b'
        r'|\bplace\s*of\s*supply\b|\btype\s*of\s*supply\b'
        r'|\boriginal\b|\bduplicate\b|\btriplicate\b'
        r'|\bterms\b|\bpayment\b|\bdelivery\b'
        r'|\btax\s*invoice\b|\btax\s*bill\b'
        r'|\bsupplier\b|\bseller\b|\bvendor\b'
        r'|\bparticulars\b|\bdescription\b|\bhsn\b'
        r'|\bquantity\b|\brate\b|\bamount\b|\btotal\b'
        r'|\bcgst\b|\bsgst\b|\bigst\b|\bcess\b'
        r'|\bround\s*off\b|\bgrand\s*total\b'
        r'|\bmode\b|\bsupply\b|\bsubject\b|\bjurisdiction\b'
        r'|\bauthorized\b|\bauthorised\b|\bsignatory\b|\bsignature\b'
        r'|\bless\b|\bnons\b|\bform\b|\bsold\b|\bbought\b'
        r'|\bregister\b|\bregistration\b|\bgstin\b|\bref\b'
        r'|\bs no\b|\bsrl\b|\bsr no\b|\bitem\b'
        r'|\bvalid\s*upto\b|\bvalid\s*until\b'
        r'|\be-mail\b|\bmobile\b|\bphone\b|\btel\b'
        r'|\bproduct\b|\bitem\b|\bdesc\b|\bqty\b|\buom\b'
        r'|\bl\s*to\s*b\b|\bbilled\s*to\b|\bshipped\s*to\b'
        r'|\bpayable\b|\bbalance\b|\bdue\b|\boverdue\b'
        r'|\bnote\b|\bremark\b|\bremark\b'
        r'|\bfor\b|\bbank\b|\bbranch\b|\bifsc\b|\bac\b'
        r'|\beway\s*bill\b|\bchallan\b|\bdoc\b|\bdoc\s*no\b'
        r'|\bnagpur\b|\bmumbai\b|\bdelhi\b|\bchennai\b|\bkolkata\b'
        r'|\bbangalore\b|\bhyderabad\b|\bpune\b|\bjaipur\b|\bagra\b'
        r'|\blucknow\b|\bpatna\b|\b Indore\b|\bbhopal\b|\bvaranasi\b'
        r'|\bnavi\b|\bthane\b|\bnavimumbai\b|\bkalyan\b'
        r'|\bmaharashtra\b|\bgujarat\b|\brajasthan\b|\bmadhya\b'
        r'|\bpradesh\b|\bkarnataka\b|\btamil\b|\bnadu\b|\btelangana\b'
        r'|\bharyana\b|\bpunjab\b|\bup\b|\bbihar\b|\bwest\s*bengal\b'
        r'|\bodisha\b|\bassam\b|\bkerala\b|\bchhattisgarh\b|\bjharkhand\b'
        r'|\bhimachal\b|\bgoa\b|\bmanipur\b|\bmeghalaya\b|\bnagaland\b'
        r'|\btripura\b|\bmizoram\b|\barunachal\b|\bsikkim\b|\butterakhand\b'
        r'|\bjammu\b|\bkashmir\b|\bladakh\b|\bchandigarh\b|\bpondicherry\b'
        r'|\bdaman\b|\bdiu\b|\blakshadweep\b|\bandaman\b|\bnicobar\b'
        r'|\broad\b|\bstreet\b|\bnagar\b|\bpark\b|\bsquare\b'
        r'|\bcolony\b|\bphase\b|\bblock\b|\bsector\b|\bward\b'
        r'|\bpin\s*code\b|\bstate\b|\bcity\b|\bcountry\b'
        r'|\bfrom\b|\bto\b|\bconsignee\b|\bbuyer\b'
        r'|\bc\/o\b|\bc\.o\b|\bflat\b|\bdoor\b|\bfloor\b|\bsuite\b'
        r'|\bbuilding\b|\bcomplex\b|\barea\b|\blocality\b|\bvillage\b'
        r'|\bdistrict\b|\btehsil\b|\btaluka\b|\bpost\b|\bpo\b|\bpolice\b'
        r'|\bstation\b|\bmain\b|\bnear\b|\bbeside\b|\bbehind\b|\bopp\b'
        r'|\bopposite\b|\bfront\b|\bground\b|\bfirst\b|\bsecond\b'
        r'|\bthird\b|\bupper\b|\blower\b|\bleft\b|\bright\b'
        r'|\bphone\s*no\b|\bmobile\s*no\b|\bemail\b|\be-mail\b'
        r'|\bpan\s*no\b|\bgst\s*no\b|\btin\b|\bvat\b|\bcst\b'
        r'|\bfreight\b|\bpacking\b|\bloading\b|\bunloading\b'
        r'|\binsurance\b|\bdiscount\b|\brebate\b|\bexcise\b'
        r'|\bservice\s*tax\b|\bcst\b|\bvat\b'
        r'|\bnos\b|\bnos\b|\bper\b|\bset\b|\bpcs\b|\bkg\b|\bgm\b|\bltr\b'
        r'|\bpanipat\b|\bludhiana\b|\bmeerut\b|\bkanpur\b|\bns\b'
        r'|\bhappy\b|\bnew\b|\bold\b|\bbest\b|\btop\b|\bbig\b|\bnew\b'
        r'|\bpvt\b|\bltd\b|\bllp\b|\bco\b|\bcomp\b|\bcompany\b'
        r'|\bsold\s*by\b|\bmanufactured\s*by\b|\bmarketed\s*by\b'
        r'|\bcountry\s*of\s*origin\b|\bfor\s*export\b'
        r'|\bapprox\b|\bdistance\b|\bkm\b|\bvalid\s*upto\b'
        r'|\bsupply\s*type\b|\btransaction\s*type\b'
        r'|\bgenerated\s*by\b|\bgenerated\s*date\b'
        r'|\beway\s*bill\s*details\b|\beway\s*bill\s*no\b'
        r'|\baddress\s*details\b|\bgoods\s*details\b'
        r'|\bproduct\s*name\b|\btaxable\s*amt\b|\btax\s*rate\b'
        r'|\bcode\b|\binvoice\s*value\b|\btotal\s*value\b'
        r'|\bdiscount\b|\bdisc\b|\bamount\b|\brate\b|\bqty\b'
        r'|\bnos\b|\bmtr\b|\bkg\b|\bgs\b|\bltr\b|\bpc\b|\bpcs\b'
        r'|\bhsn\b|\bsac\b|\bdescription\b|\bparticulars\b'
        r'|\bbatch\b|\blot\b|\bserial\b|\bmodel\b|\bpart\s*no\b'
        r'|\breverse\s*charge\b|\bsection\b|\bact\b'
        r'|\bpayable\b|\bbalance\b|\bcredit\b|\bdebit\b'
        r'|\bnote\b|\bremark\b|\breference\b'
        r'|\bdespatched\b|\bdespatch\b|\bdispatched\b'
        r'|\bnos\b|\bmtr\b|\bkg\b|\bgs\b|\bltr\b|\bpc\b|\bpcs\b'
        r'|\bunit\b|\bper\s*unit\b|\bper\s*set\b|\bper\s*piece\b'
        r'|\b1\s*nos\b|\b2\s*nos\b|\b3\s*nos\b|\b4\s*nos\b|\b5\s*nos\b'
        r'|\b1\s*set\b|\b2\s*set\b|\b1\s*pc\b|\b2\s*pc\b'
        r'|\bcolour\b|\bcolor\b|\bsize\b|\bweight\b|\bvolume\b'
        r'|\blength\b|\bwidth\b|\bheight\b|\bdepth\b'
        r'|\bincl\b|\bincl\b|\bwith\b|\bwithout\b'
        r'|\bprev\b|\bprevious\b|\bnext\b|\bcurr\b|\bcurrent\b'
        r'|\bbasic\b|\bbase\b|\badditional\b|\bextra\b'
        r'|\bnet\b|\bgross\b|\btotal\b|\bsub\s*total\b'
        r'|\bin\s*words\b|\bin\s*figures\b'
        r'|\bbank\s*name\b|\bbank\s*ac\b|\bbank\s*details\b'
        r'|\bbene\s*name\b|\bbeneficiary\b'
        r'|\bsac\b|\bhsn\s*code\b', re.IGNORECASE
    )

    _product_re = re.compile(
        r'processor|motherboard|cabinet|monitor|keyboard|mouse|printer|scanner|'
        r'laptop|desktop|tablet|\bram\b|\bssd\b|\bhdd\b|\bcpu\b|\bgpu\b|\bups\b|'
        r'chipset|module|inverter|battery|adapter|cable|'
        r'furniture|chair|sofa|bed|'
        r'tv|led|lcd|\bac\b|air.?con|cooler|fan|exhaust|'
        r'toner|cartridge|refill|'
        r'pipe|valve|fitting|flange|bolt|nut|screw|'
        r'graphics|smps|ddr\b|nvme|hdmi|vga|display.?port|'
        r'pen\s*drive|hard\s*disk|cctv|camera|solar|panel|'
        r'stabilizer|transformer|contactor|relay|fuse|mcb|'
        r'led\s*bulb|tube\s*light|exhaust\s*fan|ceiling\s*fan|'
        r'water\s*purifier|ro\s*plant|uv\s*lamp|'
        r'washing\s*machine|refrigerator|freezer|microwave|oven|'
        r'split\s*ac|window\s*ac|portable\s*ac|'
        r'gadget|device|equipment|machine|tool|instrument', re.IGNORECASE
    )

    _chinese_re = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\U00020000-\U0002a6df\U0002a700-\U0002b73f\U0002b740-\U0002b81f\U0002b820-\U0002ceaf\U0002ceb0-\U0002ebef\U00030000-\U0003134f]')

    _confidence_threshold = 20

    def _score_candidate(text, box):
        clean = text.strip().lstrip(":\uff1a\u00a0").strip()
        if len(clean) < 2:
            return None

        if _chinese_re.search(clean):
            return None

        if re.match(r'^[\d\s\-/\.:]+$', clean):
            return None

        if skip_pattern.search(clean):
            return None

        if _product_re.search(clean):
            return None

        if skip_words and any(w in clean.lower() for w in skip_words):
            return None

        if len(clean) > max_len:
            return None

        if clean.count(",") > max_commas:
            return None

        if re.search(r'\w\.\s*\w', clean):
            return None

        clean_no_parens = re.sub(r'\([^)]*\)', '', clean).strip()
        if len(clean_no_parens) < 3:
            return None
        if sum(c.isdigit() for c in clean_no_parens) > max_nums:
            return None

        box_height = max(pt[1] for pt in box) - min(pt[1] for pt in box)

        score = box_height

        return (box_height, clean)

    candidates = []
    for text, box in zip(texts, boxes):
        box_top = min(pt[1] for pt in box)
        if box_top > top_quarter:
            continue
        result = _score_candidate(text, box)
        if result:
            candidates.append(result)

    if not candidates:
        return "UnknownName"
    candidates.sort(key=lambda x: x[0], reverse=True)
    best_score = candidates[0][0]
    if best_score < _confidence_threshold:
        return "UnknownName"
    name = candidates[0][1]
    name = re.sub(r'\([\w\s\-/&]+\)', '', name).strip()
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', '_', name).strip('_')
    return name
