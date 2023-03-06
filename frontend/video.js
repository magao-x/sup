import { Blosc, GZip, Zlib, LZ4, Zstd } from 'numcodecs';

async function foo() {
    
    const codec = new Blosc(); 
    // or Blosc.fromConfig({ clevel: 5, cname: 'lz4', shuffle: Blosc.SHUFFLE, blocksize: 0 });
    
    const size = 100000;
    const arr = new Uint32Array(size);
    for (let i = 0; i < size; i++) {
      arr[i] = i;
    }
    
    const bytes = new Uint8Array(arr.buffer);
    console.log(bytes);
    // Uint8Array(400000) [0, 0, 0, 0,  1, 0, 0, 0,  2, 0, 0, 0, ... ]
    
    const encoded = await codec.encode(bytes);
    console.log(encoded);
    // Uint8Array(3744) [2, 1, 33, 4, 128, 26, 6, 0, 0, 0, 4, 0, ... ]
    
    const decoded = await codec.decode(encoded);
    console.log(new Uint32Array(decoded.buffer));
    // Uint32Array(100000) [ 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,  ... ]

}

window.foo = foo;

// peer connection
var pc = null;

// data channel
var dc = null, dcInterval = null, lastMessage = null;

function createPeerConnection() {
    var config = {
        sdpSemantics: 'unified-plan'
    };

    if (document.getElementById('use-stun').checked) {
        config.iceServers = [{urls: ['stun:stun.l.google.com:19302']}];
    }

    pc = new RTCPeerConnection(config);

    // register some listeners to help debugging
    pc.addEventListener('icegatheringstatechange', function() {
        console.log("icegatheringstatechange " + pc.iceGatheringState);
    }, false);

    pc.addEventListener('iceconnectionstatechange', function() {
        console.log("iceconnectionstatechange " + pc.iceConnectionState);
    }, false);

    pc.addEventListener('signalingstatechange', function() {
        console.log("signalingstatechange " + pc.signalingState);
    }, false);

    

    return pc;
}

function negotiate() {
    return pc.createOffer().then(function(offer) {
        return pc.setLocalDescription(offer);
    }).then(function() {
        // wait for ICE gathering to complete
        return new Promise(function(resolve) {
            if (pc.iceGatheringState === 'complete') {
                resolve();
            } else {
                function checkState() {
                    if (pc.iceGatheringState === 'complete') {
                        pc.removeEventListener('icegatheringstatechange', checkState);
                        resolve();
                    }
                }
                pc.addEventListener('icegatheringstatechange', checkState);
            }
        });
    }).then(function() {
        var offer = pc.localDescription;

        console.log("offer.sdp", offer.sdp);
        return fetch('/offer', {
            body: JSON.stringify({
                sdp: offer.sdp,
                type: offer.type,
            }),
            headers: {
                'Content-Type': 'application/json'
            },
            method: 'POST'
        });
    }).then(function(response) {
        return response.json();
    }).then(function(answer) {
        console.log("sdp answer", answer.sdp);
        return pc.setRemoteDescription(answer);
    }).catch(function(e) {
        alert(e);
    });
}

function start() {
    document.getElementById('start').style.display = 'none';

    pc = createPeerConnection();

    // navigator.mediaDevices.getUserMedia({
    //     video: true,
    //     audio: true,
    // }).then((gumStream) => {
    // for (const track of gumStream.getTracks()) {
    //     pc.addTrack(track);
    //     }
    // });
      

    var time_start = null;

    function current_stamp() {
        if (time_start === null) {
            time_start = new Date().getTime();
            return 0;
        } else {
            return new Date().getTime() - time_start;
        }
    }

    dc = pc.createDataChannel(
        "shmim2web",
        {
            ordered: false,
            maxRetransmits: 0
        }
    );
    dc.addEventListener("open", () => console.log("data channel open"));
    dc.addEventListener("close", () => console.log("data channel closed"));
    dc.addEventListener("message", (x) => {
        lastMessage = x;
        console.log("data channel message", x);
    });


    negotiate();

    document.getElementById('stop').style.display = 'inline-block';
}

function stop() {
    document.getElementById('stop').style.display = 'none';

    // close data channel
    if (dc) {
        dc.close();
    }

    // close transceivers
    if (pc.getTransceivers) {
        pc.getTransceivers().forEach(function(transceiver) {
            if (transceiver.stop) {
                transceiver.stop();
            }
        });
    }

    // close local audio / video
    pc.getSenders().forEach(function(sender) {
        sender.track.stop();
    });

    // close peer connection
    setTimeout(function() {
        pc.close();
    }, 500);
}

document.getElementById("start").addEventListener("click", start);
document.getElementById("stop").addEventListener("click", stop);