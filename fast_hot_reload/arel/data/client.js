
function arel_connect(isReconnect = false) {
  let _ws_reconnect_message = parseFloat("$arel::WS_RECONNECT_INTERVAL");
  let ws_reconnect_message = _ws_reconnect_message, reconnectInterval = _ws_reconnect_message

const ws = new WebSocket("$arel::WS_URL");

function log_info(msg) {
  console.info(`$arel::WS_MESSAGE_PREFIX ${msg}`.trim());
}

ws.onopen = function () {
  if (isReconnect) {
    // The server may have disconnected while it was reloading itself,
    // e.g. because the app Python source code has changed.
    // The page content may have changed because of this, so we don't
    // just want to reconnect, but also get that new page content.
    // A simple way to do this is to reload the page.
    window.location.reload();
    return;
  }

  log_info("$arel::WS_CONNECTED_MESSAGE");
};

ws.onmessage = function (event) {
  if (event.data === "reload") {
    window.location.reload();
  }
};

// Cleanly close the WebSocket before the page closes (1).
window.addEventListener("beforeunload", function () {
  ws.close(1000);
});

ws.onclose = function (event) {
  if (event.code === 1000) {
    // Side-effect of (1). Ignore.
    return;
  }

  log_info(
    `$arel::WS_RECONNECT_MESSAGE`
  );

  setTimeout(function () {
    const isReconnect = true;
    arel_connect(isReconnect);
  }, _ws_reconnect_message * 1000);
};
}

arel_connect();