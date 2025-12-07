#!/usr/bin/env python3

import os
import sys
import json
import inspect
import subprocess
import collections

from typing import Dict, List
from datetime import datetime

SHOW_KEY_RESEARCH_AREAS = True  # Set to False to hide the section # SRA added 09-08-2025
SHOW_ENGINEERING_PROJECTS = True  # Set to False to hide the section # SRA added 09-25-2025


Config = collections.namedtuple(
    "Config", ["verbosity", "prefix", "target", "templates"]
)


def cleanup():
    for f in [
        f"{config.target}/index.html",
        f"{config.target}/news.html",
        f"{config.target}/pubs.html",
        f"{config.target}/main.css",
    ]:
        try:
            os.remove(f)
        except Exception as _:
            pass


# for printing with colours
class bcolors:
    SUCCESS = "\033[92m"
    OKCYAN  = "\033[96m"
    OKBLUE  = "\033[94m"
    WARNING = "\033[93m"
    ERROR   = "\033[91m"
    BOLD    = "\033[1m"
    ENDC    = "\033[0m"


# Helper functions
def status(msg: str, priority=1):
    if priority <= config.verbosity:
        if priority == 0:
            divider = "*" * len(msg)
            msg     = f"{divider}\n{msg}\n{divider}"
            print(f"{bcolors.BOLD}{bcolors.OKBLUE}{msg}{bcolors.ENDC*2}")
        elif priority == 1:
            print(f"{bcolors.BOLD}{bcolors.OKCYAN}{msg}{bcolors.ENDC*2}")
        else:
            print(f"{bcolors.OKCYAN}{msg}{bcolors.ENDC}")


def success(msg: str):
    msg     = f"SUCCESS: {msg}"
    divider = "*" * len(msg)
    msg     = f"{divider}\n{msg}\n{divider}"

    print(f"{bcolors.SUCCESS}{msg}{bcolors.ENDC}")


def warning(msg: str):
    msg     = f"WARNING: {msg}"
    divider = "*" * len(msg)
    msg     = f"{divider}\n{msg}\n{divider}"

    print(f"{bcolors.WARNING}{msg}{bcolors.ENDC}")


def error(msg: str):
    msg     = f"ERROR: {msg}"
    divider = "*" * len(msg)
    msg     = f"{divider}\n{msg}\n{divider}"

    print(f"{bcolors.ERROR}{msg}{bcolors.ENDC}")
    cleanup()
    exit(1)


def warn_if_not(cond: bool, msg: str):
    if not cond:
        warning(msg)


def fail_if_not(cond: bool, msg: str):
    if not cond:
        error(msg)


def fill_if_missing(json: Dict[str, str], field: str, default=""):
    if not field in json:
        json[field] = default

    return json


def is_rakins(name):
    try:
        repo_url = subprocess.getoutput(
            f'git -C "{config.prefix}" config --get remote.origin.url'
        ).split()[0]
    except Exception as _:
        repo_url = ""

    rakins_url  = "https://github.com/rknahmed0/rknahmed0.github.io.git" # SRA changed 12/30/2022 to HTTPS protocol vs SSH
    rakins_name = "Syed Rakin Ahmed"
    
    return name == rakins_name and repo_url == rakins_url


def check_tracker(tracker):
    status("- Sanity check on tracker script")

    fail_if_not(
        "rknahmed0" not in tracker,
        "Please use your own tracker in data/meta.json",
    )


def check_cname():
    status("- Sanity check on CNAME")

    path = os.path.join(config.target, "CNAME")
    try:
        with open(path) as f:
            cname = f.read()
    except Exception as _:
        status(f"  - Couldn't load CNAME---treating it as empty.", 1)
        cname = ""

    fail_if_not(
        "syedrakinahmed.com" != cname, f"Please use your own CNAME at {path}"
    )


def read_data(json_file_name: str, optional: bool):
    path = os.path.join(config.prefix, json_file_name)
    try:
        with open(path) as f:
            status(f"- loading {path}")
            data = json.load(f)
    except Exception as _:
        fail_if_not(
            optional,
            f"Failed to parse {path}. Check your commas, braces, and if the file exists.",
        )
        # fail_if_not will exit if needed so the code below will only run if this data is optional
        status(f"Failed to load {path}---treating it as empty.", 0)
        data = {}

    return data


def read_template(template_file_name: str, optional: bool):
    path = os.path.join(config.prefix, template_file_name)
    try:
        with open(path) as f:
            status(f"- loading {path}")
            data = f.read()
    except Exception as _:
        fail_if_not(optional, f"Failed to read {path}. Does it exist?")
        # fail_if_not will exit if needed
        status(f"Couldn't load {path}---treating it as empty.", 0)
        data = ""

    return data


def write_file(file_name: str, contents: str):
    path = os.path.join(config.prefix, file_name)
    if contents == "":
        return

    with open(path, "w") as target:
        status(f"- writing {path}")
        target.write(contents)


def replace_placeholders(text: str, map: Dict[str, str]):
    newtext = text

    for k in map:
        newtext = newtext.replace(k + "-placeholder", map[k])

    return newtext


# Define functions for website pieces


def header(has_dark):
    if has_dark:
        button = """<label class="switch-mode">
    <input type="checkbox" id="mode">
    <span class="slider round"></span>
</label>
<script src="mode.js"></script>
"""
    else:
        button = ""

    out = '<header><div id="scroller"></div>\n%s</header>\n' % button

    return out


def build_news(news: List[Dict[str, str]], count: int, standalone: bool):
    if count > len(news):
        count = len(news)

    if count <= 0:
        return ""

    status("\nAdding news:")
    news_list = ""

    for n in news[:count]:
        status("- " + n["date"])
        item  = '<div class="news-item">\n'
        item += '<div class="news-left">' + n["date"] + "</div>\n"
        item += '<div class="news-right">' + n["text"] + "</div>\n"
        item += "</div>\n"
        news_list += item

    news_html = '<div class="section">\n'

    if count != len(news):
        link = '<a href="./news.html">See all posts</a>'
        news_html += (
            '<h1>Recent News <small style="font-weight: 300; float: right; padding-top: 0.23em">(%s)</small></h1>\n'
            % link
        )
    elif standalone:
        link = '<a href="./index.html">%s</a>' % meta_json["name"]
        news_html += (
            '<h1>News <small style="font-weight: 300; float: right; padding-top: 0.23em">%s</small></h1>\n'
            % link
        )
    else:
        news_html += "<h1>News</h1>\n"

    news_html += '<div class="hbar"></div>\n'
    news_html += '<div id="news">\n'
    news_html += news_list
    news_html += "</div>\n"  # close news
    news_html += "</div>\n"  # close section

    return news_html


# Helper function to decide what publication sections to include
def get_pub_titles(pubs: List[Dict[str, str]]):
    titles = set()
    for p in pubs:
        titles.add(p["section"])

    return sorted(list(titles))


def some_not_selected(pubs: List[Dict[str, str]]):
    for p in pubs:
        if not p["selected"]:
            return True

    return False


def build_pubs_inner(pubs: List[Dict[str, str]], title: str, full: bool):
    if title == "":
        return ""

    pubs_list = ""

    for p in pubs:
        if title == p["section"] and (p["selected"] or full):
            status("- " + p["title"])
            item  = '<div class="paper">\n'
            item += '<div class="paper-flex">\n'
            item += '<div class="paper-details">\n'
            item += '<div class="paper-title">' + p["title"] + "</div>\n"
            item += (
                '<div class="paper-authors">'
                + ",\n".join(p["authors"].split(", "))
                + "</div>\n"
            )
            # item += '<div class="paper-conference">' + p["journal"] + "</div>\n" # SRA commented out 09-16-2022
            item += '<div class="paper-authors">' + p["journal"] + "</div>\n" # SRA addded 09-16-2022
            item += "</div>\n"  # close paper-details
            item += '<div class="paper-icons">\n'
            item += (
                '<a href="'
                + p["link"]
                + '" alt="[PDF] "><img class="paper-icon" src="%s"/><img class="paper-icon-dark" src="%s"/></a>'
                % (style_json["paper-img"], style_json["paper-img-dark"])
                if p["link"]
                else ""
            )
            item += (
                '<a href="'
                + p["extra"]
                + '" alt="[Extra] "><img class="paper-icon" src="%s"/><img class="paper-icon-dark" src="%s"/></a>'
                % (style_json["extra-img"], style_json["extra-img-dark"])
                if p["extra"]
                else ""
            )
            item += (
                '<a href="'
                + p["slides"]
                + '" alt="[Slides] "><img class="paper-icon" src="%s"/><img class="paper-icon-dark" src="%s"/></a>'
                % (style_json["slides-img"], style_json["slides-img-dark"])
                if p["slides"]
                else ""
            )
            item += (
                '<a href="'
                + p["bibtex"]
                + '" alt="[Bibtex] "><img class="paper-icon" src="%s"/><img class="paper-icon-dark" src="%s"/></a>'
                % (style_json["bibtex-img"], style_json["bibtex-img-dark"])
                if p["bibtex"]
                else ""
            )
            item += "</div>\n"  # close paper-icons
            item += "</div>\n"  # close paper-flex
            item += "</div>\n"  # close paper
            pubs_list += item

    pubs_html  = '<h3 id="%spublications"><b>%s</b></h3>' % (title, title)
    pubs_html += pubs_list

    return pubs_html


def build_pubs(pubs: List[Dict[str, str]], full: bool, title: str = None): # SRA added title parameter 09-08-2025
    if len(pubs) == 0:
        return ""

    status("\nAdding publications:")

    pubs_html = '<div class="section">\n'

    if some_not_selected(pubs) and not full:
        pubs_html += '<h1>Selected Publications <small style="font-weight: 300; float: right; padding-top: 0.23em">(<a href="./pubs.html">See all publications</a>)</small></h1>'
    elif full:
        link = '<a href="./index.html">%s</a>' % meta_json["name"]
        heading = title if title else "Publications"  # SRA added 09-08-2025
        pubs_html += (
            '<h1>%s <small style="font-weight: 300; float: right; padding-top: 0.23em">%s</small></h1>\n'
            % (heading, link) # SRA modified to include custom heading 09-08-2025
        )
    else:
        pubs_html += "<h1>Publications</h1>"

    pubs_html += '<div class="hbar"></div>\n'
    pubs_html += '<div id="publications">\n'

    titles = get_pub_titles(pubs)

    for i in range(len(titles)):
        title = titles[i]
        pubs_html += build_pubs_inner(pubs, title, full)

    pubs_html += "</div>\n"  # close pubs
    pubs_html += "</div>\n"  # close section

    return pubs_html


def build_profile(profile: Dict[str, str]):
    profile_html  = '<div class="profile">\n'

    # SRA added 09-16-2022    
    profile_html += '<div class="title">\n'
    profile_html += '<h1>Syed Rakin Ahmed, PhD</h1>\n'
    profile_html += '</div>\n'
    profile_html += '<div class="subtitle">\n'
    profile_html += '<h2>\n'

    # Forbes Badge; SRA added 12-06-2025
    profile_html += '<a href="%s" class="forbes-badge" title="Forbes 30 Under 30 2026">Forbes 30 Under 30 2026</a>' % profile["forbes"]
    profile_html += '<p>&nbsp;</p>\n'  # visible gap without changing CSS

    profile_html += '<p>\n'
    profile_html += '<a href="%s">CV</a> | ' % profile["cv"]
    profile_html += '<a href="%s">LinkedIn</a> | ' % profile["linkedin"]
    profile_html += '<a href="%s">ORCID</a> | ' % profile["orcid"]
    profile_html += '<a href="%s">Google Scholar</a> | ' % profile["scholar"]
    profile_html += '<a href="%s">Github</a>\n' % profile["github"]
    profile_html += '</p>\n'

    profile_html += '<p>\n'
    profile_html += '<a href="%s">Harvard Profile</a> | ' % profile["hvprof"]
    profile_html += '<a href="%s">Dartmouth Profile</a>\n' % profile["dmprof"]
    profile_html += '</p>\n'

    profile_html += '<p>\n'
    profile_html += 'Engineer | '
    profile_html += 'Doctor | '
    profile_html += 'Computer Scientist'
    profile_html += '</p>\n'

    profile_html += '<p>\n'
    profile_html += '<a href="%s">UHS</a> | ' % profile["uhsprof"]
    profile_html += '<a href="%s">Resident Tutor</a> | ' % profile["cabot"]
    profile_html += '<a href="%s">FiVE</a> | ' % profile["five"]
    profile_html += '<a href="%s">IV Fellow</a> | ' % profile["ivfell"]
    profile_html += '<a href="%s">NCI.gov feature</a>\n' % profile["nci"]
    profile_html += '</p>\n'
    
    profile_html += '<p>\n'
    profile_html += 'Alpha Omega Alpha | '
    profile_html += 'Phi Beta Kappa | '
    profile_html += 'Tau Beta Pi | '
    profile_html += 'Sigma Xi'
    profile_html += '</p>\n'

    profile_html += '<p>\n'
    profile_html += '<a href="%s">syedrakin_ahmed@fas.harvard.edu</a> | ' % profile["harvard"]
    profile_html += '<a href="%s">rakin@mit.edu</a> | ' % profile["mit"]
    profile_html += '<a href="%s">syed.rakin.ahmed.med@dartmouth.edu</a>\n' % profile["dartm"]
    profile_html += '</p>\n'
    
    profile_html += '<p>\n'
    profile_html += '<a href="%s">United States Medical Licensing Exam (USMLE) Step 1 Score: 260</a> (top 4 percent)' % (profile["stepone"])
    profile_html += '</p>\n'

    profile_html += '<p>\n'
    profile_html += 'SAT I: 2310 (770 CR, 770 Math, 770 Writing) | '
    profile_html += 'SAT II: 2390 (800 Math II, 800 Chem., 790 Phys.)'
    profile_html += '</p>\n'

    profile_html += '<div class="hbar"></div>\n'
    profile_html += '</h2>\n'
    profile_html += '</div>\n'

    profile_html += (
        '<img class="headshot" src="%s" alt="Headshot"/>\n' % profile["headshot"]
    )
    profile_html += profile["blurb"]

    # SRA added 06-25-2024
    profile_html += '<p>\n'
    
    # SRA 01-23-2025 edit to ensure videos are responsive to screen size
    profile_html += '<div class="videos" id="featured-videos">\n'
    profile_html += f'<div class="video">HarvardSpeech</div>\n'
    profile_html += f'<div class="video">HMSHooding</div>\n'
    profile_html += f'<div class="video">GSASDiploma</div>\n'
    profile_html += f'<div class="video">UniWideComm</div>\n'
    profile_html += f'<div class="video">DissDefense</div>\n'
    profile_html += f'<div class="video">DartmouthFinAid</div>\n'
    profile_html += '</div>\n'
    
    profile_html += '</p>\n'
    profile_html += "</div>\n"  # close profile

    return profile_html


def add_links(html: str, links: Dict[str, str]):
    status("\nAdding links:", 2)

    toreplace = sorted(links.keys(), key=len, reverse=True)

    for name in toreplace:
        pos = html.find(name)
        while pos != -1:
            prefix = html[:pos]
            suffix = html[pos:]

            open  = html[:pos].count("<a href=")
            close = html[:pos].count("</a>")

            status(f"- {name} {pos} {open} {close}", 2)
            target = name + " "
            if pos >= 0 and open == close:
                target = '<a href="%s">%s</a>' % (links[name], name)
                suffix = suffix.replace(name, target, 1)
                html   = prefix + suffix

            start = (len(prefix) - len(name)) + len(
                target
            )  # we got rid of name and replaced it with target
            tmp = html[start:].find(name)
            pos = tmp + start if tmp >= 0 else tmp

    return html


def build_index(
    profile_json : Dict[str, str],
    news_json    : List[Dict[str, str]],
    pubs_json    : List[Dict[str, str]],
    links        : Dict[str, str],
    has_dark     : bool,
):
    body_html  = "<body>\n"
    body_html += header(has_dark)

    # SRA added 09-28-2025
    body_html += '''
    <nav class="go-to-nav">
        <a href="#featured-videos">Featured Videos</a>
        <a href="#key-research-areas">Key Research Areas</a>
        <a href="#recent-news">Recent News</a>
        <a href="#selected-publications">Selected Publications</a>
        <a href="#engineering-projects">Selected Engineering Projects</a>
    </nav>
    '''

    body_html += '<div class="content">\n'

    # SRA added 06-25-2024
    profile_html = build_profile(profile_json)

    # SRA 01-23-2025 removed width="385" and height="217" to allow for responsive design
    harvard_speech = '<iframe src="https://drive.google.com/file/d/1gUfnXREFha1onxQCOCd728FaRAqFklJY/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    hms_hooding = '<iframe src="https://drive.google.com/file/d/10HesprAQXGE-RgoiKGv3XppBXMJvxxn-/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    gsas_diploma = '<iframe src="https://drive.google.com/file/d/1qTySGLPS4J4h2cvjOJy-jbPa8D6xB6_Y/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    uniwide_comm = '<iframe src="https://drive.google.com/file/d/1QBbY3yzuSKG9M6TwtodA5uXLCD2Vnruv/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    diss_defense = '<iframe src="https://drive.google.com/file/d/19PNrYMhCeQT3mbfoANbIlhCM4gKwokwZ/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'
    dartmouth_finaid = '<iframe src="https://www.youtube.com/embed/VLV_LlrPOuI?start=290&end=515" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>'

    profile_html = profile_html.replace("HarvardSpeech", harvard_speech)
    profile_html = profile_html.replace("HMSHooding", hms_hooding)
    profile_html = profile_html.replace("GSASDiploma", gsas_diploma)
    profile_html = profile_html.replace("UniWideComm", uniwide_comm)
    profile_html = profile_html.replace("DissDefense", diss_defense)
    profile_html = profile_html.replace("DartmouthFinAid", dartmouth_finaid)

    body_html += profile_html

    # Key Research Areas Section (toggle with SHOW_KEY_RESEARCH_AREAS) # SRA added 09-08-2025
    if SHOW_KEY_RESEARCH_AREAS:
        body_html += '''
        <section class="key-research-areas" id="key-research-areas">
            <h1>Key Research Areas</h1>
            <div class="research-areas-row">
                <a href="cervical.html" class="research-area">
                    <img src="images/cervical.jpg" alt="Globally Deployed Cervical Cancer AI">
                    <div class="caption">Globally Deployed Cervical Cancer AI</div>
                </a>
                <a href="brain.html" class="research-area">
                    <img src="images/brain.jpg" alt="AI/DL in Brain Tumors">
                    <div class="caption">AI/DL in Brain Tumors</div>
                </a>
                <a href="comptumorbiology.html" class="research-area">
                    <img src="images/comptumorbiology.jpg" alt="Computational Imaging for Tumor Biology">
                    <div class="caption">Computational Imaging for Tumor Biology</div>
                </a>
                <a href="techdl.html" class="research-area">
                    <img src="images/techdl.jpg" alt="Technical AI/DL Advances">
                    <div class="caption">Technical AI/DL Advances</div>
                </a>
            </div>
        </section>
        '''    
    body_html += '<div id="recent-news">'
    body_html += build_news(news_json, 16, False) # 12/06/2025 changed from 15 to 16 news items
    body_html += '</div>'
    body_html += '<div id="selected-publications">'
    body_html += build_pubs(pubs_json, False)
    body_html += '</div>'

    # Engineering Projects Section (toggle with SHOW_ENGINEERING_PROJECTS) # SRA added 09-25-2025
    if SHOW_ENGINEERING_PROJECTS:
        body_html += '''
        <section class="engineering-projects" id="engineering-projects">
            <h1>Selected Engineering Projects</h1>
            <div class="projects-row">
                <a href="cervical.html" class="project-card">
                    <img src="images/cervical.jpg" alt="Globally Deployed Cervical Cancer AI">
                    <div class="caption">Globally Deployed Cervical Cancer AI</div>
                </a>
                <a href="aoar.html" class="project-card">
                    <img src="images/aoar.jpg" alt="AOAR - Autonomous Obstacle Avoiding Robot">
                    <div class="caption">AOAR - Autonomous Obstacle Avoiding Robot</div>
                </a>
                <a href="spinal.html" class="project-card">
                    <img src="images/spinal.jpg" alt="Spinal Cavity Creator">
                    <div class="caption">Spinal Cavity Creator</div>
                </a>
                <a href="stirling.html" class="project-card">
                    <img src="images/stirling.jpg" alt="Stirling Engine">
                    <div class="caption">Stirling Engine</div>
                </a>
            </div>
        </section>
        '''    

    body_html += "</div>\n"
    body_html += footer_html
    body_html += "</body>\n"

    index_page  = "<!DOCTYPE html>\n"
    index_page += '<html lang="en">\n'
    index_page += head_html + "\n\n"
    index_page += body_html
    index_page += "</html>\n"

    return inspect.cleandoc(add_links(index_page, links))


def build_news_page(
    news_json: List[Dict[str, str]], links: Dict[str, str], has_dark: bool
):
    content = build_news(news_json, len(news_json), True)

    if content == "":
        return ""

    body_html  = "<body>\n"
    body_html += header(has_dark)
    body_html += '<div class="content">\n'
    body_html += content
    body_html += "</div>\n"
    body_html += footer_html
    body_html += "</body>\n"

    news_html  = "<!DOCTYPE html>\n"
    news_html += '<html lang="en">\n'
    news_html += head_html + "\n\n"
    news_html += body_html
    news_html += "</html>\n"

    return inspect.cleandoc(add_links(news_html, links))


def build_pubs_page(
    pubs_json: List[Dict[str, str]], links: Dict[str, str], has_dark: bool, title: str = None # SRA added title parameter 09-08-2025
):
    content = build_pubs(pubs_json, True, title) # SRA modified to pass title 09-08-2025

    if content == "":
        return ""

    body_html  = "<body>\n"
    body_html += header(has_dark)
    body_html += '<div class="content">\n'
    body_html += content
    body_html += "</div>\n"
    body_html += footer_html
    body_html += "</body>\n"

    pubs_html  = "<!DOCTYPE html>\n"
    pubs_html += '<html lang="en">\n'
    pubs_html += head_html + "\n\n"
    pubs_html += body_html
    pubs_html += "</html>\n"

    return inspect.cleandoc(add_links(pubs_html, links))

# SRA added 09-29-2025
def build_project_page(media_html, has_dark: bool, overview: str = None, title: str = None):
    body_html  = "<body>\n"
    body_html += header(has_dark)
    body_html += '<div class="content">\n'
    if "cervical" in title.lower():
        body_html += (
            '<h1 style="display: flex; align-items: center; justify-content: space-between;">'
            'Globally Deployed Cervical Cancer AI'
            '<a href="cervicalpubs.html" class="highlighted-link" style="margin-left: 1em;">Publications</a>'
            '</h1>\n'
        )
    else:
        body_html += f'<h1>{title}</h1>\n'
    body_html += f'<p class="project-overview">{overview}</p>\n'
    body_html += '<hr>\n'
    body_html += media_html
    body_html += "</div>\n"
    body_html += footer_html
    body_html += "</body>\n"

    page_html  = "<!DOCTYPE html>\n"
    page_html += '<html lang="en">\n'
    page_html += head_html + "\n\n"
    page_html += body_html
    page_html += "</html>\n"

    return inspect.cleandoc(page_html)


if __name__ == "__main__":
    config = Config(
        verbosity = int(sys.argv[1]) if len(sys.argv) > 1 else 0,
        prefix    = os.path.dirname(os.path.abspath(__file__)), # SRA changed 12/30/2022 to use abspath
        target    = "docs",
        templates = "templates",
    )

    cleanup()

    # Load json files
    status("Loading json files:")

    meta_json = read_data("data/meta.json", optional=False)
    fail_if_not("name" in meta_json, 'Must include a "name" in data/meta.json!')
    fail_if_not(
        "description" in meta_json, 'Must include a "description" in data/meta.json!'
    )
    fail_if_not("favicon" in meta_json, 'Must include a "favicon" in data/meta.json!')
    fill_if_missing(meta_json, "tracker")

    style_json = read_data("data/style.json", optional=False)
    fail_if_not(
        "font-color" in style_json, 'Must include a "font-color" in data/style.json!'
    )
    fail_if_not(
        "background-color" in style_json,
        'Must include a "background-color" in data/style.json!',
    )
    fail_if_not(
        "header-color" in style_json,
        'Must include a "header-color" in data/style.json!',
    )
    fail_if_not(
        "accent-color" in style_json,
        'Must include a "accent-color" in data/style.json!',
    )
    fail_if_not(
        "link-hover-color" in style_json,
        'Must include a "link-hover-color" in data/style.json!',
    )
    fail_if_not(
        "divider-color" in style_json,
        'Must include a "divider-color" in data/style.json!',
    )
    fail_if_not(
        "paper-img" in style_json, 'Must include a "paper-img" in data/style.json!'
    )
    fail_if_not(
        "extra-img" in style_json, 'Must include a "extra-img" in data/style.json!'
    )
    fail_if_not(
        "slides-img" in style_json, 'Must include a "slides-img" in data/style.json!'
    )
    fail_if_not(
        "bibtex-img" in style_json, 'Must include a "bibtex-img" in data/style.json!'
    )

    fill_if_missing(style_json, "font-color-dark", style_json["font-color"])
    fill_if_missing(style_json, "background-color-dark", style_json["background-color"])
    fill_if_missing(style_json, "header-color-dark", style_json["header-color"])
    fill_if_missing(style_json, "accent-color-dark", style_json["accent-color"])
    fill_if_missing(style_json, "link-hover-color-dark", style_json["link-hover-color"])
    fill_if_missing(style_json, "divider-color-dark", style_json["divider-color"])
    fill_if_missing(style_json, "paper-img-dark", style_json["paper-img"])
    fill_if_missing(style_json, "extra-img-dark", style_json["extra-img"])
    fill_if_missing(style_json, "slides-img-dark", style_json["slides-img"])
    fill_if_missing(style_json, "bibtex-img-dark", style_json["bibtex-img"])

    profile_json = read_data("data/profile.json", optional=False)
    fail_if_not(
        "headshot" in profile_json,
        'Must include a "headshot" field in data/profile.json!',
    )
    fail_if_not(
        "blurb" in profile_json, 'Must include a "blurb" field in data/profile.json!'
    )
    fail_if_not("cv" in profile_json, 'Must include a "cv" field in data/profile.json!')
    # fail_if_not(
    #     "email" in profile_json, 'Must include a "email" field in data/profile.json!'
    # )
    fail_if_not(
        "scholar" in profile_json,
        'Must include a "scholar" field in data/profile.json!',
    )

    # These next four can be empty
    news_json = read_data("data/news.json", optional=True)
    for news in news_json:
        fail_if_not(
            "date" in news,
            'Must include a "date" field for each news in data/news.json!',
        )
        fail_if_not(
            "text" in news,
            'Must include a "text" field for each news in data/news.json!',
        )

    dates = [datetime.strptime(n["date"], "%m/%Y") for n in news_json]
    warn_if_not(
        dates == sorted(dates, reverse=True),
        "The dates in data/news.json are not in order.",
    )

    pubs_json = read_data("data/pubs.json", optional=True)
    for pub in pubs_json:
        fail_if_not(
            "title" in pub,
            'Must include a "title" field for each pub in data/pubs.json!',
        )
        fail_if_not(
            "journal" in pub,
            'Must include a "journal" field for each pub in data/pubs.json!',
        )
        fail_if_not(
            "authors" in pub,
            'Must include a "authors" field for each pub in data/pubs.json!',
        )

        fill_if_missing(pub, "link")
        fill_if_missing(pub, "extra")
        fill_if_missing(pub, "slides")

        fail_if_not(
            "section" in pub,
            'Must include a "section" field for each pub in data/pubs.json!',
        )
        fail_if_not(
            "selected" in pub,
            'Must include a "selected" field for each pub in data/pubs.json!',
        )

    auto_links_json = read_data("data/auto_links.json", optional=True)

    # Sanity checks
    if not is_rakins(meta_json["name"]):
        status("\nPerforming sanity checks:")
        check_cname()
        check_tracker(meta_json["tracker"])

    # Load templates
    status("\nLoading template files:")
    main_css    = read_template(f"{config.templates}/main.css", optional=False)
    light_css   = read_template(f"{config.templates}/light.css", optional=False)
    dark_css    = read_template(f"{config.templates}/dark.css", optional=True)
    dark_css    = light_css if dark_css == "" else dark_css
    has_dark    = light_css != dark_css
    head_html   = read_template(f"{config.templates}/head.html", optional=False)
    footer_html = read_template(f"{config.templates}/footer.html", optional=False)

    if is_rakins(meta_json["name"]):
        footer_html = """\n<footer>\n<p>Copyright &copy; 2023 Syed Rakin Ahmed</p>\n</footer>\n"""
    else:
        footer_html = "\n" + footer_html

    # Create HTML and CSS
    head_html   = replace_placeholders(head_html, meta_json)
    footer_html = replace_placeholders(footer_html, meta_json)
    main_css    = replace_placeholders(main_css, style_json)
    light_css   = replace_placeholders(light_css, style_json)
    dark_css    = replace_placeholders(dark_css, style_json)
    news_page   = build_news_page(news_json, auto_links_json, has_dark)
    pubs_page   = build_pubs_page(pubs_json, auto_links_json, has_dark)
    index_page  = build_index(
        profile_json, news_json, pubs_json, auto_links_json, has_dark
    )

    # SRA added 09-08-2025
    # Define your research area mapping (area name in your pubs.json)
    RESEARCH_AREAS = [
        ("cervicalpubs", "Globally Deployed Cervical Cancer AI"),
        ("brain", "AI/DL in Brain Tumors"),
        ("comptumorbiology", "Computational Imaging for Tumor Biology"),
        ("techdl", "Technical AI/DL Advances"),
    ]

    # For each research area, filter pubs and generate a page
    for area_slug, area_title in RESEARCH_AREAS:
        # Filter publications for this area (assuming 'area' field in pubs.json matches area_title)
        area_pubs = [pub for pub in pubs_json if pub["area"] == area_title]
        if not area_pubs:
            continue  # Skip if no publications for this area

        # Build the page using your existing function
        area_page = build_pubs_page(area_pubs, auto_links_json, has_dark, title=area_title)

        # Write the file (e.g., docs/ai-oncology.html)
        write_file(f"{config.target}/{area_slug}.html", area_page)

    # SRA added 09-25-2025, build project page function call
    
    # cervical_project_page
    cervical_media = '''
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/cervical.jpg" alt="Globally Deployed Cervical Cancer AI">
        </div>
        <div class="project-media-col">
            <iframe src="https://drive.google.com/file/d/1BOL5sjguCvMZNisrRf-nZVZz10kFKSZN/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>
    </div>
    '''
    cervical_overview = "In this project, I led the AI arm of a global consortium (PAVE) to build the first generalizable AI-driven cervical cancer screening and treatment pipeline deployed in the field. Cervical cancer is the leading cause of cancer death (>90%) in women in many low-income countries, yet entirely preventable if caught early. Using a custom colposcope-thermocoagulator, <a href=\"https://doi.org/10.1093/jnci/djaf054\">my pipeline has already been used to screen 25,000+ women across 9 countries</a>, including Brazil, Cambodia, Dominican Republic, El Salvador, Eswatini, Honduras, Malawi, Nigeria, and Tanzania, bringing lifesaving early detection to populations previously without access. For women who would otherwise wait months or years for care, this means answers and treatment in a single visit. <a href=\"cervicalpubs.html\">Publications generated from this work are highlighted here</a> as well as below, with seminal work encapsulating the <a href=\"https://doi.org/10.1038/s41598-023-48721-1\">multi-stage, comprehensive development of the diagnostic classifier</a>, <a href=\"https://doi.org/10.1371/journal.pdig.0000364\">external validation and generalizability assessment across multiple devices and geographies</a>, and the <a href=\"https://doi.org/10.1038/s41598-025-90024-0\">development/validation of the quality classifier</a>. Our study design is highlighted in <a href=\"https://doi.org/10.7554/eLife.91469.2\">this paper</a>, while preliminary results of screening using my pipeline is highlighted <a href=\"https://doi.org/10.1093/jnci/djaf054\">here</a>. This work has also received national coverage in an <a href=\"https://www.cancer.gov/about-nci/organization/cbiit/news-events/news/2024/nci-study-tests-performance-ai-based-cervical-cancer-screening\">NCI.gov feature</a>"
    cervical_proj_page = build_project_page(cervical_media, has_dark, cervical_overview, "Globally Deployed Cervical Cancer AI")
    write_file(f"{config.target}/cervicalproject.html", cervical_proj_page)

    # aoar_project_page
    aoar_media = '''
    <div class="project-media-row">
        <div class="project-media-col">
            <iframe src="https://drive.google.com/file/d/1C_keaB16Q-QUNBrw4q7Q2-x1MJO60Im-/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>    
    </div>
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/aoar/AOAR_1.jpg" alt="AOAR - Autonomous Obstacle Avoiding Robot">
        </div>
        <div class="project-media-col">
            <img src="images/aoar/AOAR_2.jpg" alt="AOAR - Autonomous Obstacle Avoiding Robot">
        </div>
    </div>
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/aoar/AOAR_3.jpg" alt="AOAR - Autonomous Obstacle Avoiding Robot">
        </div>
        <div class="project-media-col">
            <img src="images/aoar/AOAR_4.jpg" alt="AOAR - Autonomous Obstacle Avoiding Robot">
        </div>    
    </div>
    '''
    aoar_overview = "In this project, I iteratively designed an Autonomous Obstacle Avoiding Robot that autonomously detects obstacles by ultrasound sensors and avoids obstacles by moving multi-directionally via servomotors, using a free-programmable-gate-array (FPGA) coded by VHDL on VIVADO as the controller to interface between the ultrasound rangefinders and servomotors. I used a top-down, modular design and a bottom-up implementation approach, with rigorous testing conducted on each module using various digital tools (VIVADO, Digital Oscilloscope). Obstactle avoidance forms the fundamental basis of self-driving cars, as demonstrated by Waymo (Google/Alphabet Inc.)"
    aoar_page = build_project_page(aoar_media, has_dark, aoar_overview, "AOAR - Autonomous Obstacle Avoiding Robot")
    write_file(f"{config.target}/aoar.html", aoar_page)

    # SCC_project_page
    scc_media = '''
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/spinal/SCC_1.jpg" alt="Spinal Cavity Creator">
        </div>
        <div class="project-media-col">
            <img src="images/spinal/SCC_2.jpg" alt="Spinal Cavity Creator">
        </div>
    </div>
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/spinal/SCC_a.jpg" alt="Spinal Cavity Creator">
        </div>
        <div class="project-media-col">
            <img src="images/spinal/SCC_b.jpg" alt="Spinal Cavity Creator">
        </div>    
    </div>
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/spinal/SCC_c.jpg" alt="Spinal Cavity Creator">
        </div>
        <div class="project-media-col">
            <img src="images/spinal/SCC_d.jpg" alt="Spinal Cavity Creator">
        </div>    
    </div>
    '''
    scc_overview = "In this project, I iteratively designed (via CAD, 3D Printing and Machining) a Spinal Cavity Creator capable of removing cylindrical-shaped intervertebral disc space material to aid TLIF surgeries for Degenerative Spondylolisthesis. Specifically, this involved conducting a modular design approach as part of 4 distinct teams: 1. Mechanical, responsible for design of the actual mechanical drill bit and shaft interfaced to a pneumatic drill chuck, together with a guide and mount attached to a spinal cross-linker and an arm that would guide a linear stage containing the drill chuck, 2. Image Guidance, responsible for writing scripts to enable determination of the correct trajectory for drilling via image registration using pre-op MRI and real-time CT images, 3. Sensing, responsible for design of appropriate electronic/mechanical sensing equipment that would prevent contact with blood vessels and nerve roots near the foramen, and, 4. Testing, responsible for design of a fully-integrated test-bench for testing each of the aforementioned modules and verifying operation of the fully assembled drill."
    scc_page = build_project_page(scc_media, has_dark, scc_overview, "Spinal Cavity Creator")
    write_file(f"{config.target}/spinal.html", scc_page)

    # stirling_project_page
    stirling_media = '''
    <div class="project-media-row">
        <div class="project-media-col">
            <iframe src="https://drive.google.com/file/d/1x-kqwjVWc1MQ2qYLutdQ2-NsWfEUZADu/preview" frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
        </div>    
    </div>
    <div class="project-media-row">
        <div class="project-media-col">
            <img src="images/stirling/STE_1.jpg" alt="Stirling Engine">
        </div>
        <div class="project-media-col">
            <img src="images/stirling/STE_2.jpg" alt="Stirling Engine">
        </div>
    </div>
    '''
    stirling_overview = "In this project, I iteratively designed and successfully tested a Stirling engine - this involved skills including but not limited to 3 axes milling, 2 axes lathing, laser cutting, CAD and SolidWorks, 3D printing and welding, and subsequently won class competition for most efficient and fastest running Stirling engine."
    stirling_page = build_project_page(stirling_media, has_dark, stirling_overview, "Stirling Engine")
    write_file(f"{config.target}/stirling.html", stirling_page)

    # Combined_Cervical_Page - SRA added 09/29/2025
    
    # Extract the overview/media section from cervical_proj_page
    start_content = cervical_proj_page.find('<div class="content">') + len('<div class="content">')
    end_content = cervical_proj_page.rfind('</div>')
    overview_media_section = cervical_proj_page[start_content:end_content]
    
    # Extract the publications section from cervical_pubs_html
    cervical_pubs = [pub for pub in pubs_json if pub["area"] == "Globally Deployed Cervical Cancer AI"]
    cervical_pubs_page = build_pubs_page(cervical_pubs, auto_links_json, has_dark)
    start_pubs = cervical_pubs_page.find('<div class="section">')
    end_pubs = cervical_pubs_page.rfind('</div>') + len('</div>')
    pubs_section = cervical_pubs_page[start_pubs:end_pubs] if start_pubs != -1 and end_pubs != -1 else cervical_pubs_page
    
    # Build the combined page
    body_html  = "<body>\n"
    body_html += header(has_dark)
    body_html += '<div class="content">\n'
    body_html += overview_media_section
    body_html += pubs_section
    body_html += "</div>\n"
    body_html += footer_html
    body_html += "</body>\n"

    page_html  = "<!DOCTYPE html>\n"
    page_html += '<html lang="en">\n'
    page_html += head_html + "\n\n"
    page_html += body_html
    page_html += "</html>\n"

    write_file(f"{config.target}/cervical.html", inspect.cleandoc(page_html))

    # Write to files
    status("\nWriting website:")
    write_file(f"{config.target}/index.html", index_page)
    write_file(f"{config.target}/news.html", news_page)
    write_file(f"{config.target}/pubs.html", pubs_page)
    write_file(f"{config.target}/main.css", main_css)
    write_file(f"{config.target}/light.css", light_css)
    write_file(f"{config.target}/dark.css", dark_css)

    # Got to here means everything went well
    msg = f"Open {config.target}/index.html in your browser to see your website!"
    success(msg)
    exit(0)
