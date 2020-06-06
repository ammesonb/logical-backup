<h2 align="center">Logical Backup</h2>

<p align="center">
  <a href="https://travis-ci.com/ammesonb/logical-backup"><img alt="Build Status" src="https://travis-ci.com/ammesonb/logical-backup.svg?branch=master"></a>
  <a href="https://codecov.io/gh/ammesonb/logical-backup">
    <img src="https://codecov.io/gh/ammesonb/logical-backup/branch/master/graph/badge.svg" />
  </a>
  <a href="https://pyup.io/repos/github/ammesonb/logical-backup/"><img src="https://pyup.io/repos/github/ammesonb/logical-backup/shield.svg" alt="Updates" /></a>
  <a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
  <a href="https://github.com/ammesonb/logical-backup/blob/master/LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-purple.svg"></a>
</p>

<hr>

<h2>Background</h2>
I run a cloud backup, as many of us do.
However, with several terabytes of data (picture collections, digitized music over the years, etc.), restoration can take some time.
I've recently had to restore a significant amount of that data, which has taken longer than I would like.
While I can back this up incrementally to local hard drives, I do not have one single drive large enough to contain the (increasing) amount of data.

To this end, this utility will have a "state" file which is capable of spanning multiple physical hard drives.
It has a robust design for ensuring files are not changed from initial back up, to eventual (potential) restoration.

<p color="red">
NOTE: it will assume any file on the hard drive is correct, EVEN IF IT HAS BEEN CORRUPTED IN SOME WAY.
This will NOT ensure your local file system is in a good state!
</p>

<h2>Usage</h2>
To come, as development continues
