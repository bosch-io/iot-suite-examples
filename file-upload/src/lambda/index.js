/*
                           Bosch.IO Example Code License
                               Version 1.1, May 2020

Copyright 2020 Bosch.IO GmbH (“Bosch.IO”). All rights reserved.

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the
following disclaimer in the documentation and/or other materials provided with the distribution.

BOSCH.IO PROVIDES THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO
THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU. SHOULD THE PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF
ALL NECESSARY SERVICING, REPAIR OR CORRECTION. THIS SHALL NOT APPLY TO MATERIAL DEFECTS AND DEFECTS OF TITLE WHICH
BOSCH.IO HAS FRAUDULENTLY CONCEALED. APART FROM THE CASES STIPULATED ABOVE, BOSCH.IO SHALL BE LIABLE WITHOUT
LIMITATION FOR INTENT OR GROSS NEGLIGENCE, FOR INJURIES TO LIFE, BODY OR HEALTH AND ACCORDING TO THE PROVISIONS OF
THE GERMAN PRODUCT LIABILITY ACT (PRODUKTHAFTUNGSGESETZ). THE SCOPE OF A GUARANTEE GRANTED BY BOSCH.IO SHALL REMAIN
UNAFFECTED BY LIMITATIONS OF LIABILITY. IN ALL OTHER CASES, LIABILITY OF BOSCH.IO IS EXCLUDED. THESE LIMITATIONS OF
LIABILITY ALSO APPLY IN REGARD TO THE FAULT OF VICARIOUS AGENTS OF BOSCH.IO AND THE PERSONAL LIABILITY OF BOSCH.IO’S
EMPLOYEES, REPRESENTATIVES AND ORGANS.
*/

const AWS = require('aws-sdk');

const s3 = new AWS.S3();

const basicAuth = process.env.AUTHORIZATION;
const s3bucket = "bucket-name"

function handleEvent(event) {
    const blobInfo = validateRequest(event);
    switch (event.requestContext.http.method) {
        case 'POST':
            const url = generatePresignedUrl(blobInfo.deviceId, blobInfo.blobId);
            return createResponse(url, blobInfo.blobId);
        default:
            throw Error("This operation is not supported");
    }
}

function validateRequest(event) {
    let errorMessage = '';
    if (!event.headers.hasOwnProperty('device-id')) {
        errorMessage += ' device-id in headers is missing.';
    }
    if (!event.hasOwnProperty('body')) {
        errorMessage += ' request body is missing.';
    } else {
        const bodyJson = JSON.parse(event.body);
        if (!bodyJson.hasOwnProperty('blobId')) {
            errorMessage += ' blobId in body is missing.';
        }
        if (!bodyJson.hasOwnProperty('blobType')) {
            errorMessage += ' blobType in body is missing.';
        }
        if (errorMessage.length === 0) {
            return {
                blobId: bodyJson.blobId,
                blobType: bodyJson.blobType,
                deviceId: event.headers['device-id']
            };
        }
    }
    throw Error(errorMessage);
}

function generatePresignedUrl(deviceId, blobId) {
    const params = {Bucket: s3bucket, Key: `${deviceId}/${blobId}`, Expires: 3600};
    return s3.getSignedUrl('putObject', params);
}

function createResponse(url, blobId) {
    return {
        uploadURL: url,
        blobId,
        additionalInfo: {}
    };
}

exports.handler = async (event, context) => {
    console.log('Received event:', JSON.stringify(event, null, 3));

    let body;
    let statusCode = '200';
    const headers = {
        'Content-Type': 'application/json',
    };

    try {
        if (event.headers.authorization !== basicAuth) {
            return {
                statusCode: '401',
                body: 'Unauthorized',
                headers
            };
        }
        body = handleEvent(event);
       
    } catch (err) {
        statusCode = '400';
        body = err.message;
    } finally {
        body = JSON.stringify(body);
    }

    return {
        statusCode,
        body,
        headers,
    };
};
