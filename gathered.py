import requests
from lxml import html
from itertools import permutations

basic = {
    "Red": "R",
    "Blue": "U",
    "Green": "G",
    "White": "W",
    "Black": "B"
}

altAbbr = dict(basic)

altAbbr["Colorless"] = "C"
altAbbr["Snow"] = "S"
altAbbr["Phyrexian"] = "P"

for color in basic.keys():
    altAbbr["Phyrexian "+color] = "{"+basic[color]+"/P}"

for color in basic.keys():
    altAbbr["Two or "+color] = "{2/"+basic[color]+"}"

for dual in permutations(basic.keys(),2):
    altAbbr[dual[0] + " or " + dual[1]] = "{" + basic[dual[0]] + "/" + basic[dual[1]] + "}"

def gather(name):

    card = dict()

    page = requests.get("http://gatherer.wizards.com/Pages/Card/Details.aspx",{"name": name})
    tree = html.fromstring(page.content)

    pageTest = tree.xpath("//form[contains(@action,'Default')]")
    if len(pageTest) > 0:
        page = requests.get("http://gatherer.wizards.com/Pages/Card/Default.aspx",{"name": "+[" + name + "]", "sort": "rating+"})
        lucky = tree.xpath("//a[contains(@id,'cardTitle')]/text()")
        if len(lucky) == 0:
            return None
        name = lucky[0]

        page = requests.get("http://gatherer.wizards.com/Pages/Card/Details.aspx",{"name": name})
        tree = html.fromstring(page.content)

        pageTest = tree.xpath("//form[contains(@action,'Default')]")

    text = tree.xpath("//div[contains(@id,'nameRow')]/div[@class='value']/text()")
    split = len(text)>1
    if(split):
        card["name"] = text[0].strip() + " // " + text[1].strip()
    else:
        card["name"] = text[0].strip()


    text = tree.xpath("//div[contains(@id,'textRow')]/div[@class='value']/node()")

    s = ""
    for i in text:
        if str(type(i)) == "<class 'lxml.html.HtmlElement'>":
            if i.tag == "div":
                if i.text is not None:
                    s += i.text.strip()
                    if i.text.strip()[-1] not in {'"', "'", "{", "(", "["} and len(i)>0:
                        s += " "
                nested = list()
                for e in i:
                    nested.insert(0,e)
                while len(nested) > 0:
                    e = nested.pop()
                    if str(type(e)) == "<class 'lxml.html.HtmlElement'>":
                        if "alt" in e.keys():
                            t = e.get("alt")
                            if t in altAbbr.keys():
                                t = altAbbr[t]
                            s += t
                            if e.tail is not None:
                                s += e.tail
                            continue
                        if e.tag == "i":
                            s += e.text
                            for inner in e:
                                x = len(nested)
                                nested.insert(0,inner)
                            continue
                    s += str(e)
                s += "\n"
                continue
        s += str(i).strip()
        if s != "":
            s += "\n//\n"
    if s.strip() == "":
        card["text"] = None
    else:
        card["text"] = s.strip()

    text = tree.xpath("//div[contains(@id,'typeRow')]/div[@class='value']/text()")
    card["types"] = text[0].strip().replace(" \u2014","-")
    if len(text) > 1:
        card["types"] += " // "
        card["types"] += text[1].strip().replace(" \u2014","-")

    text = tree.xpath("//div[contains(@id,'manaRow')]/div[@class='value']/node()")

    s = ""

    for i in text:
        if str(type(i)) == "<class 'lxml.html.HtmlElement'>":
            if "alt" in i.keys():
                t = i.get("alt")
                if t in altAbbr.keys():
                    t = altAbbr[t]
                s += t
                continue
        s += str(i).strip()
    if s == "":
        card["cost"] = None
    else:
        card["cost"] = s

    text = tree.xpath("//div[contains(@id,'ptRow')]/div[@class='value']/text()")
    if len(text) > 0:
        card["PT"] = text[0].strip()
        if len(text) > 1:
            card["PT"] += " // "
            card["PT"] += text[1].strip()
    else:
        card["PT"] = None

    text = tree.xpath("//div[contains(@id,'cmcRow')]/div[@class='value']/text()")
    if len(text) > 0:
        card["CMC"] = int(text[0].strip())
    else:
        card["CMC"] = 0

    text = tree.xpath("//img[contains(@id,'cardImage')]")
    card["imagepath"] = "http://gatherer.wizards.com"+text[0].get("src")[5:]

    return card

def toString(card):
    if card:
        s = ""
        s += card["name"]
        if card["cost"]:
            s += ": " + card["cost"]
        s += "\n"
        s += card["types"]
        if card["text"]:
            s += "\n" + card["text"]
        if card["PT"]:
            s += "\n" + card["PT"]
        return s
    else:
        return "No card found"

def getImageData(card):
    return requests.get(card["imagepath"]).content