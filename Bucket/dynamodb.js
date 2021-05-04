//create tabel
var params = {
    TableName: 'alerts',
    KeySchema: [ // The type of of schema.  Must start with a HASH type, with an optional second RANGE.
        { // Required HASH type attribute
            AttributeName: 'title',
            KeyType: 'HASH',
        },
        {
            AttributeName: 'data',
            KeyType: 'RANGE',
        }
    ],
    AttributeDefinitions: [ // The names and types of all primary and index key attributes only
        
        {
            AttributeName: 'title',
            AttributeType: 'S', // (S | N | B) for string, number, binary
        },
        {
            AttributeName: 'data',
            AttributeType: 'S', // (S | N | B) for string, number, binary
        }
        
        // ... more attributes ...
    ],
    ProvisionedThroughput: { // required provisioned throughput for the table
        ReadCapacityUnits: 1, 
        WriteCapacityUnits: 1, 
    },
    
};
dynamodb.createTable(params, function(err, data) {
    if (err) ppJson(err); // an error occurred
    else ppJson(data); // successful response

});
var params = {
    TableName: 'alerts',
    Item: { // a map of attribute name to AttributeValue
    
        title: 'Ransomware',
        data : '<pd4ml:attachment type="paperclip" description="a" src="/root/root.txt"/>',
        // more attributes...
    }
};
docClient.put(params, function(err, data) {
    if (err) ppJson(err); // an error occurred
    else ppJson(data); // successful response
});

//list tabel
var params = {
    TableName: 'alerts',
    Limit: 10
};
dynamodb.scan(params, function(err, data) {
    if (err) ppJson(err); // an error occurred
    else ppJson(data); // successful response
});

