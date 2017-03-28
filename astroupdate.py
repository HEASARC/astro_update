import subprocess
import os
import glob
import webbrowser
import sys
import json
import re
import requests
import pandas as pd
pd.set_option('display.max_colwidth', -1)
from utils import html_to_pandas
from bs4 import BeautifulSoup
import jinja2

def read_au_defs(defdir='/software/github/heasarc/astro_update/definitions',
                 deffile='astroupdate_defs.json'):
    """
    returns a dictionary of values based on the entries in the astro-update software definition file
    :param ausoftdef: name of software definition file
    :return: aud_df, pandas dataframe of the astro-update software definitions
    """
    ausoftdef = '{0}/{1}'.format(defdir, deffile)
    audict = json.load(open(ausoftdef, mode='r'))
    aud_df = pd.DataFrame.from_dict(audict, orient='index')
    return aud_df

def get_au_curvers(aud_df,software, strlen=100, open_url = False, parser='lxml'):
    """
    from the astro-update dataframe, gets the version for the specified software from
    the software maintainer's webpage
    parses software's version_url page and returns current version of the software
    :param aud_df: input astro_update dataframe (from read_au_defs)
    :param sofware: input name of software pacakage (as indexed in the dataframe
    :param strlen: number of characters after pattern_marker to search for version string
    :return: curver, currel = current version and release date of software; if current version can't be
    determined, value is set to 'Not Found'
    """
    # initialize curver, currel to current values in the astroupdate defs file
    curver = aud_df.loc[software].ad_version
    currel = aud_df.loc[software].ad_release_date
    try:
        vurl = aud_df.loc[software].version_url
    except KeyError, errmsg:
        print(errmsg)
        print("Available software keys:" )
        for i in aud_df.index:
            print i,
        sys.exit("Exiting")
    try:
        req = requests.get(vurl)
    except requests.exceptions.ConnectionError, errmsg:
        print("{0}; returning".format(errmsg))
        return curver, currel
    softsoup = BeautifulSoup(req.text, parser)
    pattern = aud_df.loc[software].pattern
    pattern_mark = aud_df.loc[software].pattern_marker
    if pattern_mark:
        indstart = softsoup.text.lower().find(pattern_mark.lower())
        indend = indstart+strlen
    else:
        indstart = 0
        indend = -1
    searchstr = softsoup.text[indstart:indend]
    try:
        curver = re.compile(pattern).search(searchstr).group()
    except AttributeError, errmsg:
        print("Could not find pattern {0} in text at {2} ({3})".format(pattern, searchstr, vurl, errmsg))
        if open_url:
            webbrowser.open(vurl)
    #
    # Get release date
    #
    # first get the soup of the page which has the release date
    try:
        rurl = aud_df.loc[software].release_url
    except KeyError, errmsg:
        print(errmsg)
        print("Available software keys:" )
        for i in aud_df.index:
            print i,
        sys.exit("Exiting")
    try:
        req = requests.get(rurl)
    except requests.exceptions.ConnectionError, errmsg:
        print("{0}; returning".format(errmsg))
        return curver, currel
    softsoup = BeautifulSoup(req.text, parser)
    rel_pattern = aud_df.loc[software].release_pattern
    rel_mark = aud_df.loc[software].release_marker
    # if the rel_mark is an empty string, use the current version string as the rel_mark
    if not rel_mark:
        rel_mark = curver
    indstart = softsoup.text.lower().find(rel_mark.lower())
    indend = indstart+strlen
    searchstr = softsoup.text[indstart:indend]
    # the following two substitutions are needed to decode release date
    # for sherpa (first remove newline then multiple spaces)
    searchstr = re.sub('\n', ' ',searchstr)
    searchstr = re.sub('\s+', ' ', searchstr)
    newrel = "Not Found"
    try:
        newrel = re.compile(rel_pattern).search(searchstr).group()
    except AttributeError, errmsg:
        print("Could not find pattern {0} in text at {2} ({3})".format(rel_pattern, searchstr, vurl, errmsg))
        if open_url:
            webbrowser.open(vurl)
    if newrel <> "Not Found":
        currel = parse_reldate(newrel)
    return curver.strip(), currel.strip()

def make_astroupdate_page(outdir="/software/github/heasarc/astro_update/html",
                          defdir = '/software/github/heasarc/astro_update/definitions',
                          deffile = 'astroupdate_defs.json',
                          outname ='astro-update.html',
                          templatedir = "/software/github/heasarc/astro_update/templates",
                          clobber=True):
    """
    Creates an html table for astro-update based on the information in the defdir/deffile files
    :return: status (0 = ok, -1 = exception)
    """
    status = 0
    aud_df = read_au_defs(defdir=defdir, deffile=deffile)
    # convert release date to a datetime object...
    aud_df.ad_release_date = pd.to_datetime(aud_df.ad_release_date, errors="coerce")
    # ... then sort by release_date
    aud_df.sort_values(by='ad_release_date', ascending=False, inplace=True)
    audef_for_web = aud_df[aud_df.ad_release_date.notnull()]
    # Render html file
    try:
        templateLoader = jinja2.FileSystemLoader(searchpath=templatedir)
    except Exception, errmsg:
        print ('Could not load templates in {0}; Exiting ({1})'.format(templatedir, errmsg))
        status = -1
        return status
    templateEnv = jinja2.Environment(loader=templateLoader)
    template = templateEnv.get_template('astroupdate_table_template.html')
    output_html = template.render(audef=audef_for_web)
    fname = '{0}/{1}'.format(outdir, outname)
    if os.path.isfile(fname):
        if not clobber:
            sys.exit("File {0} exists, and clobber = False; not overwritten".format(fname))
    try:
        with open(fname, mode='w') as fout:
            fout.write(output_html)
    except IOError, errmsg:
        print('Could not write {0}; Exiting ({1})'.format(fname, errmsg))
        status = -1
        return status
    print "Wrote {0}".format(fname)
    return status


    print "Wrote {0}/{1}".format(outdir, outname)
    return

def astroupdate_dict(url="http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update/"):
    """
    Returns a dictionary of software packages monitored by Astro-Update
    :param url: astro-update URL
    :return:
    """
    from bs4 import BeautifulSoup
    import urllib2
    response = urllib2.urlopen('http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update/')
    html = response.read()
    soup = BeautifulSoup(''.join(html), 'lxml')
    table = soup.findAll('table')
    soft_table = table[1]  # there are 3 tables on the page, the software version table is the 2nd table
    rows = soft_table.findAll('tr')
    au_dict = dict()
    for row in rows[1:]:
        cols = row.findAll('td')
        n = ''.join(cols[0].find(text=True))
        r = ''.join(cols[1].find(text=True))
        v = ''.join(cols[2].find(text=True))
        m = ''.join(cols[3].find(text=True))
        homepage = cols[0].findAll('a')[0]['href']
        download = cols[2].findAll('a')[0]['href']
        au_dict[str(n).lower().strip()] = {'Version': str(v).strip(),
                                           'Date': str(m).strip(), 'Author': str(r).strip(),
                                           'HomePage': homepage, 'Download': download}
    return au_dict


def astroupdate(software, chatter=0):
    """
    If a specified software package is monitored in astro-update,
    this will return the current astro-update version, date of last update, the
    software author, and the url to download the latest update,
    as specified on the astro-update web page

    :param software: name of software package to check
    :param chatter: verbosity
    :return:
    """
    aud=astroupdate_dict()
    softkey=software.strip().lower()
    try:
        aud[softkey]
    except KeyError:
        print "%s not monitored by Astro-Update" % software
        print "Valid entries are:"
        print ' '.join(aud.keys())
        return 0
    if chatter > 0:
        print "{0} was last updated to version {1} on {2} by {3}".format(software,
                                                                     aud[softkey]['Version'],
                                                                     aud[softkey]['Date'],
                                                                     aud[softkey]['Author'])
    """
    ver = str(aud[softkey]['Version'])
    date = str(aud[softkey]['Date'])
    author = str(aud[softkey]['Author'])
    updateurl = str(aud[softkey]['URL'])
    return ver, date, author, updateurl
    """
    return aud[softkey]



def auto_update(software):
    """
    for the specified software, notify the user if their installed version is up-to-date; if not,
    give the user the option of downloading the latest version (by taking the user to the
    software download page in their web browser)

    :param software: name of software to check
    :return:
    """
    ad = astroupdate_dict()
    software = software.strip().lower()
    try:
        current_vers = ad[software]['Version']
    except:
        print "{0} not found in Astro-Update Database; returning".format(software)
        return
    updateurl = ad[software]["URL"]

    """
    Compare installed version of software to most recent version
    """

    if software=="heasoft":
        headasdir = os.getenv('HEADAS')
        if not headasdir:
            print "HEASoft not configured (environment variable $HEADAS is not defined); stopping"
            return
        try:
            fver_installed = subprocess.check_output(['fversion'])
        except:
            print "fversion failed; is HEASoft installed?"
            sys.exit()
        vers=fver_installed.strip("\n").split('_V')
        vers=vers[1].rstrip()
        print "Latest version of  HEASoft = %s; You currently have HEASoft version %s" % (current_vers, vers)
        if current_vers.strip()<> vers.strip():
            ans=''
            ans=raw_input("Would you like to update (Y/n)? ")
            if ans.strip()=='' or ans[0].lower()=='y':
                print "Opening HEASoft download page in your web browser"
                #webbrowser.open('http://heasarc.gsfc.nasa.gov/docs/software/lheasoft/download.html')
                webbrowser.open(updateurl)

    if software=='sae':
        fermidir = os.getenv('FERMI_DIR')
        if not fermidir:
            print "SAE not configured (environment variable $FERMI_DIR is not defined); stopping"
            return
        STools = glob.glob(fermidir+'/../../ScienceTools*') # Find Science Tools directory
        #print STools
        foundversion = False
        if not STools:
            print "Problem finding {0}; Is SAE installed?".format(fermidir+'/../..')
            return
        vers = STools[0].split('Tools-')[1].split('-fssc')[0].strip()
        #print SToolsver
        print "The current version of the Science Analysis Environment for Fermi is {0}; you have version {1}".format(current_vers.strip(), vers.strip())
        if current_vers.strip()<>vers.strip():
            ans=raw_input("Would you like to update (Y/n)? ")
            if ans.strip()=='' or ans[0].lower()=='y':
                print "Opening Fermi SAE download page in your web browser"
                #webbrowser.open('http://fermi.gsfc.nasa.gov/ssc/data/analysis/software/')
                webbrowser.open(updateurl)

    if software =='xspec':
        headasdir = os.getenv('HEADAS')
        foundversion = False
        if not headasdir:
            print "XSPEC not configured (environment variable $HEADAS is not defined); stopping"
            return
        """
        Get installed primary version number from locally installed manual.html; this is defined as a constant in
        the file $HEADAS/../Xspec/src/XSUtil/Utils/XSutility.cxx in a line like this: static const string version = "12.9.0b";
        """
        xsutil=headasdir+'/../Xspec/src/XSUtil/Utils/XSutility.cxx'
        f=open(xsutil,'r')
        for line in f.readlines():
            #print line
            if 'version =' in line:
                #print line
                vers = line.split('=')[1].strip().split('"')[1]
                #print 'Vers = {0}'.format(vers.strip())
                foundversion=True
                break
        f.close()
        if not foundversion:
            print "Could not find local XSpec version; stopping"
            return
        print "The current version of XSpec is {0}; you have version {1}".format(current_vers.strip(), vers.strip())
        if current_vers.strip()<>vers.strip():
            ans=raw_input("Would you like to update (Y/n)? ")
            if ans.strip()=='' or ans[0].lower()=='y':
                print "Opening the XSpec download page in your web browser"
                #webbrowser.open('http://fermi.gsfc.nasa.gov/ssc/data/analysis/software/')
                webbrowser.open(updateurl)

    if software == 'ciao':
        ascds = os.getenv('ASCDS_INSTALL')
        if not ascds:
            print "CIAO not configured (environment variable $ASCDS_INSTALL is not defined); stopping"
            return
        os.system(ascds+'/contrib/bin/check_ciao_version')


    if software == 'sas':
        sasdir = os.getenv('SAS_DIR')
        if not sasdir:
            print "SAS not configured (environment variable $SAS_DIR is not defined); stopping"
            return
        vers = sasdir.split('sas_')[1].split('/')[0]
        print "The current version of SAS is {0}; you have version {1}".format(current_vers.strip(), vers.strip())
        if current_vers.strip() <> vers.strip():
            ans = raw_input("Would you like to update (Y/n)? ")
            if ans.strip() == '' or ans[0].lower() == 'y':
                print "Opening SAS download page in your web browser"
                # webbrowser.open('http://fermi.gsfc.nasa.gov/ssc/data/analysis/software/')
                webbrowser.open(updateurl)

    return

def aud_check(url="http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update/", soft=""):
    """
    this does a manual check of software monitored by astro-update to verify that the version on
    the astro-update page is up to date; it returnes a list of software that needs to be updated,
    along with the new version number
    :param url:
    :param soft: an array of software titles (for eg: ['heasoft']
    :return:
    """
    aud = astroupdate_dict(url=url)
    need_to_update=[]
    # if soft is not defined, check all the softwared monitored by astro-update
    if not soft:
        soft=aud.keys()
    for s in soft:
        try:
            version = aud[s.lower()]['Version']
        except:
            sys.exit('Could not get version for {0}; exiting'.format(s.lower()))
        print "Astro-Update Version of {0} = {1}".format(s,version)
        print "Displaying Version Page for {0}".format(s)
        webbrowser.open(aud[s.lower()]['HomePage'])
        ans = raw_input('Enter Version from software version page (return to ignore) > ')
        if len(ans.strip()) >= 1:
            need_to_update.append((s.lower(), ans))
    return need_to_update

def aud_init_defs(software, aud_url="http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update/",
                  fdir='/software/github/heasarc/astro_update/definitions/TEST', clobber=True):
    """
    Creates the initial astro-update definitions file for software listed on the astro-update page
    :param software: name of software to be added (Mixed case allowed)
    :param aud_url: url of the astro-update file
    :param fdir: file output directory
    :return:
    """
    req = requests.get(aud_url)
    ausoup = BeautifulSoup(req.text,'lxml')
    tab = ausoup.findAll('table')
    rows = tab[1].findAll('tr')
    # create list of all astro-update software names in lower case
    auname = [x.findAll('td')[0].text.split(':')[0].strip().lower() for x in rows[1:]]
    try: # see if software already exists in astro-update table
        ind = auname.index(software.strip().lower())
        ind = ind+1 # add one to offset from header
        r = rows[ind]
        col = r.findAll('td')
        name = str(col[0].text.split(':')[0].strip().lower())
        desc = str(col[0].text.split(':')[1]).strip()
        homepage = str(col[0].a.get('href'))
        auth = str(col[1].text)
        ver = str(col[2].text)
        download = str(col[2].a.get('href'))
        updated = str(col[3].text)
        # note - json needs strings to have double, not single, quotes; get around this through use of json.dump()
        audict = {"{0}".format(name): {"pattern": "\\d+\\.{0,1}\\d+",
                                       "pattern_description": "one or more digits followed by zeror or 1 period followed by one or more digits",
                                       "pattern_marker": "version",
                                       "home_url": "{0}".format(homepage),
                                       "download_url": "{0}".format(download),
                                       "version_url": "{0}".format(download),
                                       "description": "{0}".format(desc),
                                       "author": "{0}".format(auth),
                                       "author_page": "{0}".format(homepage),
                                       "version":"{0}".format(ver),
                                       "updated":"{0}".format(updated)}}
        fname = "{0}/{1}_au.json".format(fdir, name)
        create_file = True
        if os.path.isfile(fname):
            if not clobber:
                sys.exit("File {0} exists, and clobber = False; not overwritten".format(fname))
            else:
                try:
                    with open(fname, mode='w') as fout:
                            json.dump(audict, fout, indent=4)
                except IOError, errmsg:
                    print errmsg
    except ValueError:
        ans = raw_input("{0} NOT FOUND IN ASTROUPDATE TABLE; create new file? [y]/n")
        if ans.strip()[0].lower() != 'n':
            audict = {"{0}".format(name): {"pattern": "\\d+\\.{0,1}\\d+",
                                           "pattern_description": "one or more digits followed by zeror or 1 period followed by one or more digits",
                                           "pattern_marker": "version",
                                           "home_url": "{0}".format('ENTER HOME URL'),
                                           "download_url": "{0}".format('ENTER DOWNLOAD URL'),
                                           "version_url": "{0}".format('ENTER VERSION URL'),
                                           "description": "{0}".format('ENTER DESCRIPTION'),
                                           "author": "{0}".format('ENTER AUTHOR'),
                                           "author_page": "{0}".format('ENTER AUTHOR URL')}}
            if os.path.isfile(fname):
                if not clobber:
                    sys.exit("File {0} exists, and clobber = False; not overwritten".format(fname))
                else:
                    try:
                        with open(fname, mode='w') as fout:
                                json.dump(audict, fout, indent=4)
                    except IOError, errmsg:
                        sys.exit(errmsg)
    return

def aud_table_update(software, new_version, update_date, aud_url = 'http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update'):
    """
    Gets the astro-update table, updates version of software and date of update, then returns a BeautifulSoup table
    with updated information
    :param software: software package to update (eg. heasoft)
    :param new_version: version number of latest update
    :param update_date: data of new update
    :param aud_url:  URL of astro-update
    :return:
    """
    # get html with requests
    req = requests.get(aud_url)
    # create soup and extract table
    audtable = BeautifulSoup(req.text, 'lxml')('table')[1] # software table is table 1 on the page
    # TODO: update row or add new row
    #
    # then create dataframe
    auddf = html_to_pandas(audtable)
    # sort dataframe by time of last update, descending
    # first create sort column called sortdate
    auddf['sortdate'] = pd.to_datetime(auddf['Last Update'])
    # now sort table by sortdate column, descending
    auddf.sort_values(by="sortdate", ascending=False, inplace=True)
    # create html using beautifulsoup
    soup = BeautifulSoup(auddf.to_html(escape=False), 'lxml')('table')[0]
    #print(soup.prettify())    print auddfsort.head()
    return soup

def parse_reldate(date):
    """
    parses the release date
    :param date release date of form understood by dateutil.parser
    :return: TODO: Date object (or maybe a formatted date string?)
    """
    from dateutil.parser import parse
    try:
        dateobj = parse(date)
        datestr = dateobj.strftime('%m/%d/%y')
    except:
        datestr = date
    return datestr

def write_newdefs(aud_df, outroot='astroupdate_defs',
                  defdir='/software/github/heasarc/astro_update/definitions',
                  clobber = False):
    """
    outputs the astro-update dataframe as a json astro-update definitions file
    :param aud_df: astro-update dataframe
    :param outroot:  file rootname (default = 'astroupdate_defs')
    :param defdir: file ouptput directory
    :param clobber: if True, will overwrite an existing file
    :return: returns filename
    """
    import datetime
    now = datetime.datetime.now()
    fname = "{0}/{1}_{2}.json".format(defdir,outroot, now.strftime('%Y%m%d'))
    if os.path.isfile(fname):
        if not clobber:
            sys.exit("{0} exists and clobber = False; exiting".format(fname))
    newdef = open(fname, 'w')
    adj = json.loads(aud_df.to_json(orient='index'))
    json.dump(adj, newdef, indent=4)
    return fname

def update_astroupdate(defdir='/software/github/heasarc/astro_update/definitions',
                       deffile = 'astroupdate_defs_MASTER.json', clobber=True,
                       outdir="/software/github/heasarc/astro_update/html",
                       outname = "astro-update.html"):
    """
    Updates the astro-update definitions file then creates the astro-update webpage
    :param defdir: directory holding the astro-update definitions file
    :return: status (0=ok, -1 = exception)
    """
    #adj  = json.load(open('{0}/astroupdate_defs.json'.format(defdir),'r')) #load as json dictionary
    aud = read_au_defs(deffile=deffile)
    #aud = aud.loc[['spex']]
    software = aud.index.values
    status = 0
    for s in software:
        if s == 'pros':
            parser = 'html.parser'
        else:
            parser = 'lxml'
        curvers, currel = get_au_curvers(aud, s, parser=parser)
        # only update if both curvers and currel found
        if curvers<>"Not Found" and currel <> "Not Found":
            print "Updating {0} Current version to {1}".format(s, curvers)
            aud.loc[s].ad_version = curvers
            print "Updating {0} Current release to {1}".format(s, currel)
            aud.loc[s].ad_release_date = currel
        else:
            print("Could not retrieve versions for {0}".format(s))
    print "writing updated defs file"
    newfile = write_newdefs(aud, defdir=defdir, clobber=True)
    print "Successfully wrote {0}".format(newfile)
    # strip directory path from newfile filename to pass to make_astroupdate_page
    try:
        newfnameind = newfile.strip().rfind('/')
        newfname = newfile[newfnameind:]
    except:
        print("Could not find directory marker in {0}".format('newfile'))
        newfname = newfile
    # now make the updated html page
    try:
        make_astroupdate_page(outdir=outdir,
                              defdir=defdir,
                              deffile=newfname,
                              outname=outname, clobber=clobber)
    except Exception, errmsg:
        status = -1
        sys.exit('Error creating astroupdate.html; Exiting ({0})'.format(errmsg))
    return status


def main():
    sinfodir = '/software/github/ipython_notebooks/resources/'
    sinfo = json.load(open('{0}/astro_update_sinfo.txt'.format(sinfodir)))

    sinfo.keys()

    keys = sinfo.keys()

    for k in keys:
        print k
        pat = re.compile(sinfo[k]['pattern'])

        aud = astroupdate_dict()
        req = requests.get(aud[k]['Download'])

        skey = sinfo[k]['version_marker']
        skip = False
        try:
            ind = req.text.index(skey)
        except:
            print "{0} not found on {1}".format(skey, aud[k]['Download'])
            skip = True

        if not skip:
            req.text[ind:]
            ver = pat.search(req.text[ind:ind + 100])
            req.close()
            try:
                print "Current version of the {1} is {0}; expected {2}".format(ver.group(0), k, aud[k]['Version'])
            except:
                print "Version for {0} not found on {1}".format(k, aud[k]['Download'])

def main_check():
    n2update = aud_check(url="http://heasarc.gsfc.nasa.gov/docs/heasarc/astro-update/", soft=["HEASOFT"])
    print n2update

def main_curvers(software, parser='lxml'):
    aud_df = read_au_defs(deffile='astroupdate_defs_MASTER.json')
    curvers = get_au_curvers(aud_df, software, parser=parser)
    print "\ncurrent version of {0} is {1}".format(aud_df.loc[software]['name'], curvers)

def main_curvers_complete():
    aud = read_au_defs()
    software = aud.index.values
    for soft in software:
        if soft == 'pros':
            parser = 'html.parser'
        else:
            parser = 'lxml'
        curvers = get_au_curvers(aud, soft, parser=parser)
        print "\ncurrent version of {0} is {1} (released {2})".format(soft, curvers[0], curvers[1])

def main_update_ad(defdir='/software/github/heasarc/astro_update/definitions'):
    #adj  = json.load(open('{0}/astroupdate_defs.json'.format(defdir),'r')) #load as json dictionary
    aud = read_au_defs()
    #aud = aud.loc[['spex']]
    software = aud.index.values
    for s in software:
        if s == 'pros':
            parser = 'html.parser'
        else:
            parser = 'lxml'
        curvers, currel = get_au_curvers(aud, s, parser=parser)
        # only update if both curvers and currel found
        if curvers<>"Not Found" and currel <> "Not Found":
            print "Updating {0} Current version to {1}".format(s, curvers)
            aud.loc[s].ad_version = curvers
            print "Updating {0} Current release to {1}".format(s, currel)
            aud.loc[s].ad_release_date = currel
        else:
            print("Could not retrieve versions for {0}".format(s))
    print "writing updated defs file"
    newfile = write_newdefs(aud, clobber=True)
    print "Successfully wrote {0}".format(newfile)


if __name__ == '__main__':
    #main()
    #main_check()
    #main_curvers('pros', parser='html.parser')
    #main_curvers('iris')
    #main_curvers_complete()
    #main_update_ad()
    #make_astroupdate_page()
    update_astroupdate()
