# compare.py

This Utility was created because there was a need to merge 2 code bases. 
File names and paths could be different, new files could've been added etc.


## Usage



This Utility enables us to analyze the code bases in the following way:

```bash
$ python3 compare.py -h
usage: compare.py FOLDER

Compare file names given a csv or folder

positional arguments:
  FOLDER

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program version number and exit
  -c CSV, --csv CSV     csv file that has the list of filenames to check
  -f FOLDER, --folder FOLDER
                        folder to compare
  -s SCORE, --score SCORE
                        minimum score to achieve 0 - 1
  -m MATCHES, --matches MATCHES
                        top matches
  --force               do not use cached file list
  --obj-in-installers OBJ_IN_INSTALLERS
                        given a file with the installers script names, search for DB objects/operation within those script or their children
  -t THREAD, --thread THREAD
                        number of threads to use
  --compare-simple      simple compare, exact filename
  --compare             simple compare + boyer moore compare
  --files-in-file FILES_IN_FILE
                        search within file for references of files
  --not-in-file         modifier for --files-in-file only output those that are not in the file
  --forms-files         search for Forms files (.fmb)
  --reports-files       search for Report files (.xdrz)
  --proc-files          search for Forms files (.mk/.pc)
  --sh-files            search for Forms files (.sh/ksh)
  --adf-files           search for Forms files (.ear)
```

### Get a list of all the files

```bash
$ python3 compare.py ../M_GIT/R/
load folder(s)
loading cache json
Gathering Files from: ../M_GIT/R/
wrote json: R.json
```

### Compare the all files in a folder to a given csv with a list of files

```bash
$ python3 compare.py ../M_GIT/R/ -c List.csv --compare-simple
load folder(s)
loading cache json
loaded json: R.json
load csv
From List.csv read: 1550
simple compare
wrote json: findings.json
compare.py FOLDER
```

### Compare the all files in a folder to another folder


```bash
$ python3 compare.py ../Makro_BR_GIT/RC04022_1/ -f ../Makro_BR_GIT/RC04022_1/ --compare-simple
load folder(s)
loading cache json
loaded json: RC04022_1.json
loading cache json
loaded json: RC04022_1.json
simple compare
wrote json: findings.json
```


    group.add_argument(
        "-f","--folder",
        help='folder to compare'
    )
    parser.add_argument(
        "-s","--score",
        type=float,
        default=0.7,
        help='minimum score to achieve 0 - 1'
    )
    parser.add_argument(
        "-m","--matches",
        type=int,
        default=3,
        help='top matches'
    )
    parser.add_argument(
        "--force",
        action='store_true',
        help='do not use cached file list'
    )
    parser.add_argument(
        "--obj-in-installers",
        help='given a file with the installers script names, search for DB objects/operation within those script or their children'
    )
    parser.add_argument(
        "-t","--thread",
        help='number of threads to use',
        type=int, default=1
    )
    parser.add_argument(
        "--compare-simple",
        action='store_true',
        help='simple compare'
    )
    parser.add_argument(
        "--compare",
        action='store_true',
        help='simple compare + boyer moore compare'
    )
    parser.add_argument(
        "--files-in-file",
        help='search within file for references of files'
    )

    parser.add_argument(
        "--not-in-file",
        action='store_true',
        help='modifier for --files-in-file only output those that are not in the file'
    )

    parser.add_argument(
        "--forms-files",
        action='store_true',
        help='search for Forms files (.fmb)'
    )

    parser.add_argument(
        "--reports-files",
        action='store_true',
        help='search for Report files (.xdrz)'
    )

    parser.add_argument(
        "--proc-files",
        action='store_true',
        help='search for Forms files (.mk/.pc)'
    )

    parser.add_argument(
        "--sh-files",
        action='store_true',
        help='search for Forms files (.sh/ksh)'
    )

    parser.add_argument(
        "--adf-files",
        action='store_true',
        help='search for Forms files (.ear)'
    )



boyer_moore_compare