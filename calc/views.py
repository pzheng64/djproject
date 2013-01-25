import ConfigParser

from django.shortcuts import render_to_response


#2013-01-25 Friday  (commit to master)

# Create your views here.
def index(request):
    config = ConfigParser.RawConfigParser()
    config.read('input.txt')
    
    data = config.items('section1')
        
    return render_to_response('calc/index.html', {'data':data})