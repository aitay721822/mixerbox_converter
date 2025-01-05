function getHandler(yt_app, request) {
  const extractor = (t) => t?.endpointHandlerActionMap?.["yt-service-request"];
  const handler =
    extractor(yt_app?.ytEndpointBehavior) ||
    extractor(yt_app?.ytActionHandlerBehavior) ||
    extractor(yt_app?.ytActionRouterBehavior) ||
    extractor(yt_app?.ytComponentBehavior) ||
    extractor(yt_app?.ytdAppBehavior) ||
    extractor(yt_app?.ytRendererBehavior);
  return handler(yt_app, request).ajaxPromise;
}

async function main(video_ids) {
  let yt_application = document.querySelector("ytd-app");

  let request = { addToPlaylistServiceEndpoint: { videoId: video_ids[0] } };
  let res = await getHandler(yt_application, request);
  console.log(res);

  let renderer = res?.data?.contents?.[0]?.addToPlaylistRenderer;
  if (!renderer) {
    throw new Error("取得播放清單資訊失敗");
  }

  const viewModel =
    renderer.actions?.[1]?.buttonRenderer?.command?.commandExecutorCommand
      ?.commands?.[1]?.showDialogCommand?.panelLoadingStrategy?.inlineContent
      ?.dialogViewModel?.customContent?.createPlaylistDialogFormViewModel;
  if (!viewModel) {
    throw new Error("取得 createPlaylistDialogFormViewModel 失敗");
  }
  viewModel.videoIds = video_ids;

  let add_action = video_ids.map((video_id) => {
    return {
      action: "ACTION_ADD_VIDEO",
      addedVideoId: video_id,
    };
  });

  let remove_action = video_ids.map((video_id) => {
    return {
      action: "ACTION_REMOVE_VIDEO_BY_VIDEO_ID",
      removedVideoId: video_id,
    };
  });

  renderer?.actions?.forEach((e) => {
    let endpoint =
      e?.addToPlaylistCreateRenderer?.serviceEndpoint
        ?.createPlaylistServiceEndpoint;
    if (endpoint) {
      endpoint.videoIds = video_ids;
    }
  });

  renderer?.playlists?.forEach((e) => {
    let r = e?.playlistAddToOptionRenderer;
    if (r) {
      r.containsSelectedVideos = "NONE";
      let add_endpoint = r.addToPlaylistServiceEndpoint?.playlistEditEndpoint;
      if (add_endpoint) {
        add_endpoint.actions = add_action;
      }
      let remove_endpoint =
        r.removeFromPlaylistServiceEndpoint?.playlistEditEndpoint;
      if (remove_endpoint) {
        remove_endpoint.actions = remove_action;
      }
    }
  });

  let style = {
    bubbles: !0,
    composed: !0,
    detail: {
      actionName: "yt-open-popup-action",
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
  };
  yt_application.dispatchEvent(new CustomEvent("yt-action", style));
}
