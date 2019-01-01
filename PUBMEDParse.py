import pickle
import pandas as pd
import lxml.html
from lxml.etree import tostring
import re
import itertools
import io
import json
import helper
from lxml import etree
import string
import random
import datetime

#Parse pubmed ids
def pubmed_ids(article):
    id_types_list = [elem for elem in article.xpath(".//pubmeddata/articleidlist/articleid[@idtype = 'pubmed' or @idtype = 'doi' or @idtype = 'pmc']")]
    id_dict = {}
    for id_type in id_types_list:
        id_type_name = id_type.values()[0]
        id_type_val = id_type.text_content()
        id_dict[id_type_name] = id_type_val
    return id_dict


#Parse pubmed article title
def pubmed_title(article):
    article_title = article.xpath(".//article/articletitle")[0].text_content()
    return article_title


#Parse pubmed dates
def pubmed_date(article):
    date_types_all = [elem for elem in article.xpath(".//pubmeddata/history/pubmedpubdate[@pubstatus = 'pubmed' or @pubstatus = 'entrez']")]
    big_list = []
    for date_type in date_types_all:
        child_list = [child for child in date_type.iterchildren('year','month','day')]
        child_tup = (child_list,len(child_list))
        big_list.append(child_tup)

    check_list = [b[1] for b in big_list]
    date_val_list = big_list[check_list.index(max(check_list))][0]
    date_dict = {d.tag:d.text_content() for d in date_val_list}

    if len(date_dict.values()) == 3:
        date_full = '{0}/{1}/{2}'.format(date_dict['month'],date_dict['day'],date_dict['year'])
    elif len(date_dict.values()) < 3:
        date_full = None

    return [date_dict, date_full]


#Parse mesh terms
def pubmed_mesh(article):
    mesh_list = [elem for elem in article.xpath('.//meshheadinglist/meshheading')]
    mesh_dict_list = []
    all_tags = []
    for m in mesh_list:
        mesh_dict_desc = {elem.tag:elem.text_content() for elem in m.iterchildren('descriptorname')}
        mesh_dict_qual = {elem.tag:[elem.text_content() for elem in m.iterchildren('qualifiername')] for elem in m.iterchildren('qualifiername')}
        mesh_dict = {**mesh_dict_desc, **mesh_dict_qual}
        mesh_dict_list.append(mesh_dict)
    return mesh_dict_list


#Parse keywords, in event that there are no mesh terms
def pubmed_kwd(article):
    kw_dict_list = []
    kw_list = [elem for elem in article.xpath('.//keywordlist/keyword')]
    for kw in kw_list:
        kw_dict = {"descriptorname":kw.text_content()}
        kw_dict_list.append(kw_dict)
    return kw_dict_list


#Parse abstract text
def pubmed_abstract(article):
    abs_list = [elem for elem in article.xpath('.//article/abstract/abstracttext')]
    abs_dict_list = []
    for a in abs_list:
        abs_dict = {}
        attrib_dict = a.attrib
        text_dict = {'text':a.text_content()}
        abs_dict = dict(list(attrib_dict.items())+list(text_dict.items()))
        abs_dict_list.append(abs_dict)
    return abs_dict_list


#Parse pubmed pubtypes
def pubmed_pub_type(article):
    pub_type_list = [elem.text_content() for elem in article.xpath('.//article/publicationtypelist/publicationtype')]
    return pub_type_list


#Parse journal name and abbreviation
def pubmed_journal(article):
    journal_list = [elem for elem in article.xpath(".//article/journal/title|.//article/journal/isoabbreviation")]
    journal_dict = {j.tag:j.text_content() for j in journal_list}
    return journal_dict


#Parse author information
def pubmed_author(article):
    auth_list = [elem for elem in article.xpath(".//article/authorlist/*")]
    auth_dict_list = []
    for auth in auth_list:
        auth_dict = {}
        auth_dict['fname'] = auth.xpath(".//forename")[0].text_content()
        auth_dict['lname'] = auth.xpath(".//lastname")[0].text_content()
        auth_dict['affl'] = re.sub("\d+","",auth.xpath(".//affiliation")[0].text_content())
        auth_dict_list.append(auth_dict)
    return auth_dict_list


#Define parser function
def parse_pubmed(article):

    try:
        abs_dict_list = pubmed_abstract(article)
    except:
        abs_dict_list = None
    try:
        auth_dict_list = pubmed_author(article)
    except:
        auth_dict_list = None
    try:
        dates_dict_list = pubmed_date(article)
    except:
        dates_dict_list = None
    try:
      publish_date = dates_dict_list[0]
    except:
      publish_date = None
    try:
      publish_date_full = dates_dict_list[1]
    except:
      publish_date_full = None
    try:
        id_dict = pubmed_ids(article)
    except:
        id_dict = None
    try:
        journal_dict = pubmed_journal(article)
    except:
        journal_dict = None
    try:
      journal_name = journal_dict['title']
    except:
      journal_name = None
    try:
      journal_iso = journal_dict['isoabbreviation']
    except:
      journal_iso = None
    try:
        mesh_dict_list = pubmed_mesh(article)
    except:
        try:
            mesh_dict_list = pubmed_kwd(article)
        except:
            mesh_dict_list = None
    try:
        pub_type_list = pubmed_pub_type(article)
    except:
        pub_type_list = None
    try:
        title = pubmed_title(article)
    except:
        title = None
    try:
        optionalId01 = id_dict['doi']
    except:
        optionalId01 = None
    try:
        optionalId02 = id_dict['pmc']
    except:
        optionalId02 = None



    d = {
        'title':title,
        'associatedId': id_dict['pubmed'],
        'author': auth_dict_list,
        'journalName' : journal_name,
        'journalISO':journal_iso,
        'pubtype': pub_type_list,
        'publishdate':publish_date,
        'publishdatefull':publish_date_full,
        'meshterms': mesh_dict_list,
        'abstract':abs_dict_list,
        'optionalId01' :optionalId01,
        'optionalId02': optionalId02,
        'pullsource': 'pubmed'
    }

    return d

#
# #Import serialized xml document itself by it's unique identifier
# def import_xml(path_name):
#     doc_list_path = path_name
#     with open(doc_list_path, 'rb') as f:
#         doc_list = pickle.load(f)
#     return doc_list
#
# #Convert xml into html element objects
# def xml_to_html(doc_list):
#     pre_article_list = []
#     for doc in doc_list:
#         xml = lxml.html.fromstring(doc)
#         article = xml.xpath("//pubmedarticle")
#         pre_article_list.append(article)
#         article_list = list(itertools.chain.from_iterable(pre_article_list))
#     return article_list
#
#
#Run articles through parser - throw out problematic papers
def parse_all(article_list):
  article_dict_list = []
  for art in article_list:
    try:
        d = parse_pubmed(art)
        article_dict_list.append(d)
    except:
        pass
  parsed_df = pd.DataFrame(article_dict_list)
  return parsed_df


def parse_properties(parsed_df):
  unique_id = helper.create_unique_id()
  now = datetime.datetime.now()
  time_stamp = now.strftime("%Y-%m-%d %H:%M")
  # id_list = helper.id_run('search')
  # run_fetch = self.pub_fetch(id_list)
  # article_list = helper.xml_to_html(run_fetch,self.input_db)
  n_records_parsed = len(parsed_df.index)
  prop_dict = {'id':unique_id,'id_type':'parse'
  ,'input_db':'pubmed','record_count':n_records_parsed
  ,'run_date':time_stamp}
  return prop_dict

def main():
  full_doc = helper.id_run('fetch','pubmed')
  article_list = helper.xml_to_html(full_doc,'pubmed')
  parsed_df = parse_all(article_list)
  prop_dict = parse_properties(parsed_df)
  unique_id = prop_dict['id']
  helper.serialize_output(unique_id,parsed_df)
  helper.update_id_json(prop_dict)

#
# #function to serialize the dataframe with parsed info
# def serialize_df(unique_identifier_parse,df):
#     #Serialize dataframe
#     pklName = unique_identifier_parse+'.pkl'
#     with open(pklName, 'wb') as f:
#       pickle.dump(df, f)
#
# #function to save the dataframe's unique identifier for the xml as a json
# def to_json(unique_identifier_parse):
#     json.dump(unique_identifier_parse,open("unique_identifier_parse.json","w"))
#
#
# def main(xml_path_name):
#   character_set = string.ascii_letters
#   character_set += string.digits
#
#   unique_identifier_parse = ''
#
#   for _ in range(25):
#       unique_identifier_parse += random.choice(character_set)
#
#   #Retrieve xml document
#   doc_list = import_xml(xml_path_name)
#
#   #Turn them into article (html) objects to be parsed
#   article_list = xml_to_html(doc_list)
#
#   #Parse all xml documents into dataframe
#   parsed_df = parse_all(article_list)
#
#   #Serialize parsed dataframe
#   serialize_df(unique_identifier_parse,parsed_df)
#
#   return unique_identifier_parse
#
# def ex_main_parse_pubmed(xml_path_name):
#   unique_identifier_parse = main(xml_path_name)
#   to_json(unique_identifier_parse)
#   return(unique_identifier_parse)
#
# if __name__ == '__main__':
#   unique_identifier_parse = ex_main_parse_pubmed(xml_path_name)
