import httplib, urllib
import urllib2
import cookielib
import os
import re
import sys
sys.path.append('../') 
from  conf.conf import *

host = "reviewboard.eng.vmware.com"
get_headers = {
    'Host' : 'reviewboard.eng.vmware.com',
    'Connection' : 'keep-alive' , 
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
    'Accept-Language' : 'zh-CN,zh;q=0.8,en;q=0.6',
    'Cookie':'s_vi=[CS]v1|297EE873851D1A76-6000013460010948[CE]; collapsediffs=True; rbsessionid=d6d00ca234e7a853c35aec9908beb8ad',
}
all_user = dict() #  user : review_id
review = dict() # review_id : reply_username
reply = dict() # user : reply_count
page_flag = True

# get all user from list.txt
def get_user_list():
	f = open(userlist_path + "/user.txt","r+")
	content = f.readline().strip()
	while content:
		all_user[content] = dict()
		reply[content] = 0
		all_user[content]["total_num"] = 0
		content = f.readline().strip()
	#print all_user

# get all the reviewer of each submitter
def read_user_submitter(submitter , file_name):
	fp = open(file_name, "r+")
	content = fp.readline()
	i = all_user[submitter]["total_num"]
	flag = False
	while content:
		str_find = content.find("label-submitted")
		
		if str_find >= 0:
			flag = True
			regex = re.compile(r'/r/\d*') 
			r_id = regex.findall(content)			
			all_user[submitter][i] = r_id[0]
			i += 1
			all_user[submitter]["total_num"] += 1
	
		content = fp.readline()
	return flag


# get info of one review from web
def wget_review_page(r_id): 
	_url = "%s/" % r_id
	
	rname = r_id[3:]
	review[rname] = dict()    #  each r_id  has  a dict
	file_name = "%s/%s.txt" % (review_path,rname)
	wget_html(_url,file_name)
	return file_name

# get reviews submitted by one user 
def wget_submitter_review(key,page):
	_url = "/users/%s/?page=%s" % (key, page)
	file_name = "%s/%s_%s.txt" % (source_path,key,page)
	wget_html(_url, file_name )
	return file_name

# get reviews of each user
def get_user_review(): 
	for key in all_user.keys():
		page = 1
		flag = True
		while True: # test==========================================need update
			file_name = wget_submitter_review(key,page) #real
			#file_name = "source/%s_%s.txt" % (key,page) # test
			page = page +1
			flag = read_user_submitter(key,file_name)
			if flag == False:
				break
		#print all_user

#login the web 
def post_login():
	url = '/account/login/'
	values = {
	  'username' : 'xux',
	  'password' : 'Knight1990',
	  'next_page' : '/dashboard/',
	}

	headers = {
	    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.114 Safari/537.36',
	    'Content-Type': 'application/x-www-form-urlencoded',
	    'Connection' : 'keep-alive',
	    'Cookie':'s_vi=[CS]v1|297EE873851D1A76-6000013460010948[CE]; collapsediffs=True; rbsessionid=2158c3def7071636f012ac9ecb18bf84' ,  
	    'Referer':'https://reviewboard.eng.vmware.com/account/login/',
	    'Host' : 'reviewboard.eng.vmware.com',
	    'Origin':'https://reviewboard.eng.vmware.com',
	    'Content-Type':'application/x-www-form-urlencoded',
	    'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
	}
	values = urllib.urlencode(values)
	conn = httplib.HTTPSConnection(host, 443)
	conn.request("POST", url, values, headers)
	response = conn.getresponse()

	print 'Response: ', response.status, response.reason
	hdata = response.getheaders()
	for i in xrange(len(hdata)):
		for j in xrange(len(hdata[i])):
			print hdata[i][j],
		print
	

def wget_html(_url, file_name):
	conn=httplib.HTTPSConnection(host)
	conn.request("GET",_url,None,get_headers)
	res2=conn.getresponse()
	if res2.status != 200 :
		page_flag = False

	data = res2.read()
	fp = open(file_name, "w")
	fp.write(data)
	fp.close()

#find all replyers from review info
def read_review(_path , r_name):
	#print "=============================================="
	fp = open(_path , "r+")
	content = fp.readline()
	review_count = 0
	users = dict()
	review[r_name] = dict()
	review[r_name]["user"] = dict()
	countnum = 0
	while content:
		str_find1 = content.find(">Summary:")
		str_find2 = content.find("Submitter:")
		str_find3 = content.find("class=\"reviewer\"");
		
		if str_find1 >= 0: # find topic name
			regex = re.compile(r'red\">.*')
			topic =  regex.findall(content)
			review[r_name]["topic_name"] = topic[0][5:-11]
			#print "Topic : %s " % (topic[0][5:-11])
		
		elif str_find2 >= 0:  # find topicer
			content = fp.readline()
			regex = re.compile(r'users/\w*/')
			username = regex.findall(content)
			review[r_name]["submitter"] = username[0][6:-1]
			#print "User : %s" % (username[0][6:-1])
		
		elif str_find3 >= 0: # find reviewer
			review_count += 1
			regex = re.compile(r'/users/[a-zA-Z]*/')
			reviewer = regex.findall(content)
			
			if reviewer:
				temp = reviewer[0][7:-1]
				review[r_name]["user"][countnum] = temp
				countnum += 1
				
										
		content = fp.readline()
	review[r_name]["total_num"] = review_count
	fp.close()

#get reviews submitted by each user
def read_all_review():
	for key in all_user.keys():
		num = all_user[key]["total_num"]
		i = 0
		while i < num:
			r_id = all_user[key][i]
			file_name = wget_review_page(r_id)
			rname = r_id[3:]
			read_review(file_name , rname)

			i += 1

#output numbers of review , for each user
def output_submitter_of_review():
	fp = open(result_path + "/result.txt","w")
	for key in all_user.keys():
		s =  "submitter:%s  ,  total_num: %s " % (key,all_user[key]["total_num"])
		fp.write(s+"\n")
		print s
	fp.write( "**************************************************\n")
	fp.close()

#output numbers of reply , for each user
def output_reply_of_review():
	print review
	fp = open(result_path + "/result.txt","a")
	for r in review.keys():
		if review[r].has_key("user"):
			for lag in review[r]["user"].keys():
				username = review[r]["user"][lag] 
				if(reply.has_key(username)):
					reply[username] += 1
	for u in reply.keys():
		s =  "user:%s , reply_num:%s" % (u,reply[u])
		fp.write(s+"\n")
		print s
	fp.close()



#main
if __name__ == '__main__':
	post_login()
	get_user_list()
	#read_user_submitter()
	get_user_review()
	read_all_review()
	output_submitter_of_review()
	output_reply_of_review()

