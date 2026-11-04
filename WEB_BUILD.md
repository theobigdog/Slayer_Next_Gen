# Playing Slayer in a browser (and on a tablet or phone)

The window version runs in a web browser through **pygbag**, which packs the game together with a copy of Python
that runs in the browser. Nothing in the game code needs to change; these are the steps.

## One-time setup

In a command prompt:

```
pip install pygbag
```

## Try it on your PC

From the game folder (`E:\PersonalProjects\Slayer_Next_Gen`):

```
python -m pygbag .
```

Then open **http://localhost:8000** in Chrome. The first time, it downloads the browser version of Python, so give
it a minute. Click the page once to start (browsers want a click before a game can make sound). Ctrl+C in the
command prompt stops it.

## Try it on your tablet or phone (same Wi-Fi as the PC)

```
python -m pygbag --bind 0.0.0.0 .
```

Find your PC's address with `ipconfig` (the "IPv4 Address", something like 192.168.1.23), then open
**http://192.168.1.23:8000** on the tablet. If Windows asks whether Python may use the network, allow it on private
networks. Some browsers are stricter with plain `http://` addresses that aren't localhost; if the tablet shows a blank
page, the itch.io route below (which uses https) is the fix.

## Put it on itch.io

```
python -m pygbag --build --archive .
```

That makes **build/web.zip**. On itch.io: Create new project, Kind of project: **HTML**, upload `web.zip`, tick
"This file will be played in the browser", set the viewport to **1280 x 720**, and set Visibility to **Draft** (or
Restricted) while testing. Then open the project page on any device.

## Good to know

- **Saves** live in each browser (localStorage), so a party saved on the tablet is only on the tablet.
- **Typing** on a touch screen: an on-screen keyboard appears after the first tap. On any device, the **Keyboard**
  button in the typing field shows or hides it.
- **The End**: on the web there's no window to close, so a click starts a new game.
- `pygbag.ini` keeps the saved_parties folder, the build folder and check_data.py out of the web version.
- `dev_mode()` is still on, so the web build is a dev build until that's switched off.
- Claude couldn't run the web build itself (the sandbox can't reach pygbag's download site), so the first real run
  is the real test. If something looks off, a screenshot or the browser console (F12) text helps a lot.
