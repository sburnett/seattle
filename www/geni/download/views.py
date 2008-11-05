from django.views.generic.simple import direct_to_template, redirect_to
from django.http import HttpResponse
from geni.control.models import User
from django.contrib.auth.models import User as DjangoUser
import os

genilookuppubkey = "105218563213892243899209189701795214728063009020190852991629121981430129648590559454805294602863437180197383200157929797560056350651679990894183323458702862383371519103715161824514423932881746333116028227752248782962849181124520405658625393671898781069029621867416896240848133246870330371456213657364326213813 312714756092727515598780292379395872371276579078748109351554518254514481793368058883800678614580459772002765797032260325722225376614522500847276562927611577356613250215335341049455959290730180509179381157215997103098273389151149413304651001604934784742532791625955088398372313329455355494987750365806646536736636469629655380899143568352774219563065173996594667744415518391700387531919897253828997026843423501056159275468434318826550727964420829405894564122992335715124500381230290658083672331257499145017512885259835129381157750762124840076790791959202427846549512062536039325580240373309487741134319467890746673599741871268148060727018149256387697190931523693175768595351239154192239059676450669982991614136056253025495132755577907582430428560957011063839801600705947720544745078362907393070987536242330969100531923153182335864179094051994566951914233193211513835463083579669213012962131981383521706159377642531633316767375065073795772235104272775823159971873875983352843528481287521146512180790378064962825824780897817649973221317403460404503674474228769268269759375408409701974795615072086988269846532097319019681202860566295633729260133667739837481809185531026939053693396561388528361977535344851490021470007393713971344577027977"


def __get_guser__(www_username):
    try:
        django_user = DjangoUser.objects.get(username = www_username)
    except DjangoUser.DoesNotExist:
        ret = HttpResponse("<h2>Did you mispell the username? No user with username <font color=\"red\">%s</font> exists in the GENI database.</h2>"%(www_username))
        return ret, False
    
    try:
        geni_user = User.objects.get(www_user = django_user)
        return geni_user,True
    except User.DoesNotExist:
        # this should never happen if the user registered -- show server error of some kind
        ret = HttpResponse("User registration for this user is incomplete [auth records exists, but geni user profile is absent], please contact ivan@cs.washington.edu.")
        return ret,False

def download(request,username):
    ret,success = __get_guser__(username)
    if not success:
        return ret
    return direct_to_template(request,'download/installers.html', {'username' : username})

def build_installer(username, dist_char):
    '''
    returns url to the finished installer
    dist_char is in "lwm"
    '''
    ret,success = __get_guser__(username)
    if not success:
        return False, ret
    geni_user=ret

    # prefix dir is specific to this user
    prefix = "/var/www/dist/geni/%s_dist"%(username)
    # remove and recreate the prefix dir
    os.system("rm -Rf %s/"%(prefix))
    os.system("mkdir %s/"%(prefix))

    # write out to file the user's donor key
    f = open('%s/%s'%(prefix, username),'w');
    f.write("%s"%(geni_user.donor_pubkey))
    f.close()

    # write out to file the geni lookup key
    f = open('%s/%s_geni'%(prefix, username),'w');
    f.write("%s"%(genilookuppubkey))
    f.close()
    
    # write out to file the vesselinfo to customize the installer
    vesselinfo = '''Percent 8\nOwner %s/%s\nUser %s/%s_geni\n'''%(prefix,username,prefix,username);
    f = open('%s/vesselinfo'%(prefix),'w');
    f.write("%s"%(vesselinfo))
    f.close()

    # paths to custominstallerinfo and carter's customize_installers script
    vesselinfopy = "/home/ivan/trunk/test/writecustominstallerinfo.py"
    carter_script = "/home/ivan/trunk/dist/customize_installers.py"
    
    # create the dir where vesselinfo will be created
    os.system("mkdir %s/vesselinfodir/"%(prefix))
    # create the vessel info
    cmd = "cd /var/www/dist/geni && python %s %s/vesselinfo %s/vesselinfodir 2> /tmp/customize.err > /tmp/customize.out"%(vesselinfopy, prefix, prefix)
    #f = open("/tmp/out", "w")
    #f.write(cmd)
    os.system(cmd)
    # run carter's script to create the installer of the particular type ((w)in, (l)inux, or (m)ac)
    os.system("python %s %s %s/vesselinfodir/ %s/ > /tmp/carter.out 2> /tmp/carter.err"%(carter_script, dist_char, prefix,prefix))
    #os.system("python %s %s %s/vesselinfodir/ %s/ &> /tmp/out"%(carter_script, dist_char, prefix,prefix))
    # compose and return the url to which the user needs to be redirected
    redir_url = "http://seattle.cs.washington.edu/dist/geni/%s_dist/"%(username)
    return True, redir_url

def mac(request,username):
    success,ret = build_installer(username, 'm')
    if not success:
        return ret
    redir_url = ret + "seattle_mac.tgz"
    return redirect_to(request, redir_url)

def linux(request,username):
    success,ret = build_installer(username, 'l')
    if not success:
        return ret
    redir_url = ret + "seattle_linux.tgz"
    return redirect_to(request, redir_url)

def win(request,username):
    success,ret = build_installer(username, 'w')
    if not success:
        return ret
    redir_url = ret + "seattle_win.zip"
    return redirect_to(request, redir_url)
