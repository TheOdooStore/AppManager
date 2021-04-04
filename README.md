<h1 align="center">AppManager</h1><br/>
<p align="center">
<a href="https://www.theodoostore.com/AppManager">
    <img alt="AppManager" title="AppManager" src="https://i.imgur.com/DVlt9CL.png" width="450">
  </a>
  </p>
<b>AppManager</b> is an Odoo app management tool that automatically checks for app updates so you don't have to!

## Table of Contents

- [Introduction](#TLDR)
- [Installation](#installation)
- [Features](#features)
- [Issues](#issues-and-bugs)

## TLDR
AppManager automatically checks your database it's apps to see if there are newer app versions available remotely.<br/>
We compare the installed versions on your database with the latest available apps on <a href="https://www.theodoostore.com" target="_blank">The Odoo Store</a>.<br/>
Since The Odoo Store automatically syncs thousands of apps on a daily basis, through a direct Github connector, we always know about updates!<br/>
AppManager will auto-check your apps against our platform and if updates are available you will be notified!

## Installation
1. Navigate into your custom addons path and clone this repository
```
cd /odoo14/custom/addons
git clone https://github.com/theodoostore/AppManager.git
```

2. Checkout the right directory depending on the version of your Odoo instance:
```
git checkout 14.0
```

3. Add the Github repository into your Odoo configuration file.
```
addons_path=/odoo14/odoo14-server,/some/other/paths/you/have,/odoo14/custom/addons/AppManager
```

4. Restart your Odoo instance so our new module is available
```
sudo service odoo14-server restart
```

5. Go to Apps and click on "Update Apps List"
6. Search for the app `app_manager` and install it.
7. Congrats, that's it! You now see the AppManager app available on your main Odoo screen.


## Features
# TODO: add overview screen showing the AppManager in an Odoo!
- Quick overview of apps and their statusses
- Quick button to instantly download the latest version from The Odoo Store
- Quick button to instantly download <b>and</b> update your app within the database<br/> <b>Note: this is at your own risk!</b>
- Quick navigation the details about the app on The Odoo Store
- See if apps are certified and up-to-date
- See if apps have security issues (CVE's)
- Get automatically notified about available updates


## Issues and bugs
Have an issue or a bug? Please create a new report under the <a href="https://github.com/theodoostore/app_manager/issues">"Issues"</a> section.
