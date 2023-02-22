async function build_authorization() {
    let timestamp = Math.floor(Date.now() / 1e3),
        cookies = function(cookie) {
            const data = {};
            if (cookie && "string" == typeof cookie) {
                for (let pair of cookie.split("; ")) {
                    pair = pair.split("=");
                    data[pair[0].trim()] = pair[1];
                }
            }
            return data;
        }(document.cookie);
    return (
        "SAPISIDHASH " +
        timestamp +
        "_" +
        (await (async function (data) {
            const hash = await crypto.subtle.digest("SHA-1", new TextEncoder().encode(data));
            return Array.from(new Uint8Array(hash))
                .map((b) => b.toString(16).padStart(2, "0"))
                .join("");
        })(timestamp + " " + cookies.SAPISID + " https://www.youtube.com"))
    );
}

function build_request(api_path, params, auth) {
    let ctx = window.yt?.config_ || window.ytcfg?.data_;
    if (!ctx) {
        throw new Error("yt.config_ or ytcfg.data_ not found");
    }
    
    let body = params || {};
    // adsignals
    let adsignals_string = yt.ads_.signals_.getAdSignalsString();
    let adsignals = {
        "bid": yt.ads.biscotti.lastId_,
        "params": [],
    };

    let data = adsignals_string.split('&')
    for (let i in data) {
        let pair = data[i].split('=')
        let k = pair[0],
            v = pair[1];
        if (!v) {
            v = "0"
        }

        if (k == "bid") {
            adsignals.bid = v
        } else {
            adsignals.params.push({
                key: k,
                value: decodeURIComponent(v),
            })
        }
    }
    // attach context
    body.context = {
        ... body.context,
        adSignalsInfo: adsignals,
        client: { 
            ...ctx.INNERTUBE_CONTEXT.client 
        },
        request: { 
            ...ctx.INNERTUBE_CONTEXT.request 
        },
        user: { 
            ...ctx.INNERTUBE_CONTEXT.user,
        },
    };
    console.log(body)
    
    let req = {
        method: "POST",
        mode: "same-origin",
        body: JSON.stringify(body),
        headers: {
            authorization: auth,
            "Content-Type": "application/json",
            "x-goog-authuser": 0,
            "x-goog-visitor-id": ctx.VISITOR_DATA,
            "x-goog-pageid": ctx.DELEGATED_SESSION_ID,
            "x-origin": "https://www.youtube.com",
            "x-youtube-bootstrap-logged-in": ctx.LOGGED_IN,
            'x-youtube-client-name': ctx.INNERTUBE_CONTEXT_CLIENT_NAME,
            "x-youtube-client-version": ctx.INNERTUBE_CONTEXT_CLIENT_VERSION,
        },
    };
    return new Request(`${api_path}?key=${ctx.INNERTUBE_API_KEY}`, req);
}

async function execute(api_path, params) {
    try {
        let req = build_request(api_path, params, await build_authorization());
        let res = await fetch(req);
        return res.json();
    } catch (e) {
        console.log(e);
    }
}

async function main(video_ids) {
    let res = await execute("/youtubei/v1/playlist/get_add_to_playlist", {
        'excludeWatchLater': true,
        'videoIds': [video_ids[0]],
    })

    let renderer = res?.contents?.[0].addToPlaylistRenderer;
    if (!renderer) {
        throw new Error("取得播放清單資訊失敗")
    }

    let add_action = video_ids.map((video_id) => {
        return {
            action: 'ACTION_ADD_VIDEO',
            addedVideoId: video_id,
        }
    });
    
    let remove_action = video_ids.map((video_id) => {
        return {
            action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID",
            removedVideoId: video_id,
        }
    });

    renderer?.actions?.forEach(e => {
        let endpoint = e?.addToPlaylistCreateRenderer?.serviceEndpoint?.createPlaylistServiceEndpoint;
        if (endpoint) {
            endpoint.videoIds = video_ids
        }
    });

    renderer?.playlists?.forEach(e => {
        let r = e?.playlistAddToOptionRenderer;
        if (r) {
            r.containsSelectedVideos = "NONE";
            let add_endpoint = r.addToPlaylistServiceEndpoint?.playlistEditEndpoint;
            if (add_endpoint) {
                add_endpoint.actions = add_action;
            }
            let remove_endpoint = r.removeFromPlaylistServiceEndpoint?.playlistEditEndpoint;
            if (remove_endpoint) {
                remove_endpoint.actions = remove_action;
            }
        }
    });

    let yt_application = document.querySelector("ytd-app")
    let style = {
        bubbles: !0,
        composed: !0,
        detail: {
          actionName: 'yt-open-popup-action',
          optionalAction: !1,
          args: [
            {
              openPopupAction: {
                popupType: "DIALOG",
                popup: { addToPlaylistRenderer: renderer },
              },
            },
            yt_application,
          ],
          disableBroadcast: !1,
          returnValue: [],
        },
    }
    yt_application.dispatchEvent(new CustomEvent("yt-action", style))
}