# Script: jira_elaborate.py
#
# The script elaborates a set of imported Jira issues
#
# Example:
#   python jira_elaborate.py sprtorcas_1613_security_concept_for_dds_com_tlc


import argparse
import glob
import os
import sys
from contextlib import contextmanager
import xml.etree.ElementTree as ET
from library import excepthook, load_config


teams = {
    "network" : [["Christian K�nik", "koenik"], ["Wilhelm Schmelz", "schmelz"]],
    "arobs" : [["", "taurescu"], ["Andrei-Sebastian Ungureanu", "aungureanu"]],
    "beta" : [["", "killinger"], ["Spas Nedev", "nedev"], ["", "amueller"], ["", "bittl"], ["", "di"], ["", "holkar"]],
    "iberia" : [["", "guerra"], ["", "marcet"], ["Pilar Mart�n L�pez", "pmartin"], ["", "moscat"], ["", "aguilar"], ["", "manas"]],
    "icon" : [["Carlo Camicia", "camicia"], ["", "tillier"], ["", "hochradl"], ["", "ext-atos-offenberger"], ["", "krizan"], ["", "siket"], ["Marlene Hartmann", "hartmann"]],
    "gucci" : [["Zvonimir Ive�ic", "ivesic"], ["", "tomljenovic"], ["", "ddjuranic,eborovac,crnjac"], ["", "kozic,posavi"], ["", "tcosic"]],
    "stroustrup" : [["Korbinian Hirschm�ller", "hirschmuelle"]],
    "swat" : [["Horatiu-Mihai Ghemes", "ghemes"]],
    "zazu" : [["", "pino"], ["Jose Ramon Garcia Perez", "jgarcia"], ["", "garcia"], ["", "melendez"], ["Natalia Michalak", "michalak"]],
}


def parse_arguments():
    custom_description = (
        "Elaborate Jira issues into a readable markdown summary."
    )
    custom_epilog = (
        "Examples:\n"
        "  jira sprtorcas_1613_security_concept_for_dds_com_tlc\n"
        "\n"
        "Notes:\n"
        "  - The activity folder must exist under <kb_path>/activities/<activity>.\n"
        "  - The script reads raw/jira*.xml files and writes\n"
        "    raw/jira_elaborated.gitignore.md.\n"
    )

    parser = argparse.ArgumentParser(
        description=custom_description,
        epilog=custom_epilog,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument("activity", help="Generate the 1bf only for the specified topic")
    parser.add_argument("-v", action="store_true", help="Verbose console output")

    return parser.parse_args()


def xml_get_formatted_text(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        text = list()
        for child in prop_value:
            text.append(ET.tostring(child, encoding='unicode', method='text'))
        if len(text):
            return("\\n".join(text).replace('@@@@', '&'))
        if prop_value.text:
            return(prop_value.text.replace('@@@@', '&'))
    return("None")


def xml_get_labels(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        return(','.join([child.text for child in prop_value]))
    return("None")


def xml_get_links(item, prop_name):
    links = list()
    issuelinks = item.find(prop_name)
    if issuelinks is not None:
        for issuelinktype in issuelinks:
            name = issuelinktype.find('name')
            if name is not None:
                if name.text=='Cloners':
                    continue
                outwardlinks = issuelinktype.find('outwardlinks')
                if outwardlinks is not None:
                    for issuelink in outwardlinks:
                        issuekey = issuelink.find('issuekey')
                        if issuekey is not None:
                            links.append(f"{name.text} {issuekey.text}")
                inwardlinks = issuelinktype.find('inwardlinks')
                if inwardlinks is not None:
                    for issuelink in inwardlinks:
                        issuekey = issuelink.find('issuekey')
                        if issuekey is not None:
                            reverse_link_name = f"(in){name.text}"
                            if name.text=='Implements':
                                reverse_link_name = 'Is Implemented By'
                            if name.text=='Consists (Bundle)':
                                reverse_link_name = 'Includes'
                            links.append(f"{reverse_link_name} {issuekey.text}")
        if links:
            return(', '.join(links))
    return("None")


def xml_get_text(item, prop_name):
    prop_value = item.find(prop_name)
    if prop_value is not None:
        text = prop_value.text
        if text:
            text = text.replace('@@@@', '&')
            return(text)
    return("None")


def main():
    
    sys.excepthook = excepthook

    args = parse_arguments()

    config = load_config('kb0')

    kb_path = config['kb_config']['kb_path']

    activity_dir = os.path.join(kb_path, "activities", args.activity)

    if not os.path.isdir(activity_dir):
        print(f"ERROR: Activity directory {activity_dir} does not exist.")
        sys.exit(1)

    raw_dir = os.path.join(activity_dir, "raw")

    jira_issues_files = sorted(glob.glob(os.path.join(raw_dir, "jira*.xml")))
    if not jira_issues_files:
        print(f"ERROR: No jira*.xml files found in {raw_dir}")
        sys.exit(1)
    
    team_dict = {}
    for team, team_members in teams.items():
        for team_member in team_members:
            full_name = team_member[0]
            if full_name:
                team_dict[full_name] = team

    out_content = list()
    # out_content.append(f"List of Jira tasks assigned to {'icon'}\n")
    
    seen_links = set()
    
    for jira_issues_file in jira_issues_files:
        with open(jira_issues_file, 'r', encoding='utf-8') as f:
            jira_issues_xml = f.read()

        jira_issues_xml = jira_issues_xml.replace('&', '@@@@')  # To avoid XML parsing issues

        # Parse the XML file
        try:
            tree = ET.ElementTree(ET.fromstring(jira_issues_xml))
            root = tree.getroot()
            print(f"Successfully parsed XML from {jira_issues_file}")

        except ET.ParseError as e:
            print(f"ERROR: Failed to parse XML from {jira_issues_file} - {e}")
            continue

        for child in root:
            if child.tag == 'channel':
                for item in child:  # An item is a Jira ticket
                    if item.tag!='item':
                        continue
                    title = xml_get_text(item, 'title')
                    link = xml_get_text(item, 'link')
                    
                    # Skip if we've already processed this link
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    
                    assignee = xml_get_text(item, 'assignee')
                    reporter = xml_get_text(item, 'reporter')
                    created = xml_get_text(item, 'created')
                    status = xml_get_text(item, 'status')
                    team = team_dict.get(assignee, "unknown")
                    description = xml_get_formatted_text(item, 'description')
                    labels = xml_get_labels(item, 'labels')
                    links = xml_get_links(item, 'issuelinks')

                    pass_filter = (team == "icon")
                    # if not pass_filter:
                    #     continue

                    out_content.append("")
                    out_content.append(f"Title: {title}")
                    out_content.append(f"    Link: {link}")
                    out_content.append(f"    Assignee: {assignee}")
                    out_content.append(f"    Reporter: {reporter}")
                    out_content.append(f"    Team: {team}")
                    out_content.append(f"    Created: {created}")
                    out_content.append(f"    Status: {status}")
                    out_content.append(f"    Labels: {labels}")
                    out_content.append(f"    Links: {links}")
                    # out_content.append(f"    Description: {description[:500]}")
                    out_content.append(f"    Description: {description}")

                    comments_node = item.find('comments')
                    if comments_node is not None:
                        for comment in comments_node:
                            # Get the property 'author' of the comment
                            author = comment.get('author')

                            text = []
                            for child in comment:
                                text.append(ET.tostring(child, encoding='unicode', method='text'))
                            text = "\n".join(text).replace('@@@@', '&')
                            text = text.replace('\n', '\n        ')
                            out_content.append(f"    Comment: {text}")
    
    jira_elaborated_file = os.path.join(raw_dir, "jira_elaborated.gitignore.md")

    with open(jira_elaborated_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_content))

    print(f"Processed issues saved to: {jira_elaborated_file}")


if __name__ == "__main__":
    main()

# import pdb; pdb.set_trace()


