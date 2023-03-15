# Access Submission Configs on CDC Gitlab


## Setup Instructions:

### If You Do Not Have the Tostadas Repository Cloned, There are Two Options to Initialize the Submodule and Retrieve the Submission Config Files:

### (1) Clone and Initialize Separately
```
git clone https://github.com/CDCgov/tostadas.git && cd tostadas/bin && git submodule init && git submodule update --remote
```

#### OR 

### (2) Clone with Initialization
```
git clone --recurse-submodules https://github.com/CDCgov/tostadas.git
```
### You should now have the latest submission config files available within bin/config_files

### If You Already Have Tostadas Cloned Locally + Want to Update with Latest Remote Changes, You Can Either Use the Following Command Every Time:
```
git submodule update --remote
```
### Or Permanently Modify the Git Config to Update with Remote Changes Every Time You Use ``` git pull ```
```
git config --global submodule.recurse true
```

## More Information:

:link: Internal Repository: https://git.biotech.cdc.gov/monkeypox/mpxv_annotation_submission_dev_configs.git 

** Must have access to the Monkeypox group through CDC credentials **


