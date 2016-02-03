github-recursive-clone
======================

This repo allows a user to pull a project and all its submodules though the
github API.

##configs.cfg
To get started, replace the values in configs.cfg.

####external_token
A token to a user on github enterprise. Creating this read only would be a good
idea, since this code never needs to write anything.

Read more about creating OAUTH tokens [here](https://help.github.com/articles/creating-an-access-token-for-command-line-use/)

Read more about robot users [here](https://help.github.com/articles/what-s-the-difference-between-user-and-organization-accounts/)

####internal_token
Same as above, but for an internal GHE instance

####internal_url
This is a URL as it is passed to the [github3.py](http://github3py.readthedocs.org/en/latest/github.html#githubenterprise-object)
library. If your GHE instance is code.lan, the URL would look like
http://code.lan

##Constraints

-The initial repository, and all submodules must be on a github instance

-Both keys need to be able to read any repo that gets specified. This should
not be an issue, because you probably are not making submodules of private
repos that your key cant reach.

##Docker
I reccomend running the docker with:

```shell
--dns so it can see your GHE instance
-d so its disconnected
-p **:8080 so it can grab a port on the host
--name ghrc
```

##General process

1. grab the repo
  * determine with GH its on
  * download
  * extract it in place
2. parse its .gitmodules file
3. for each module, get its URL and current sha, repeat

##JSON input:
Its currently triggered by sending JSON formated data, specifying the URL
and the sha that you are looking for. For example
```
{
    "URL":"git@github.com:paparazzi/paparazzi.git",
    "sha":"22ca42632644f7dd90ab79e0e8a5a737316a94b3"
    }
```
##Curl Examples
Some examples where we assume this code is running on http://ghrc:8080/ghrc
```shell
# Basic curl with JSON on the command line
curl -H "Content-Type: application/json" -d '{"URL":"", "sha":"40chars"}' http://ghrc:8080/ghrc -o repo.tar.gz
# Basic curl with json stored in a file
curl -H "Content-Type: application/json" -d @master.json http://ghrc:8080/ghrc -o repo.tar.gz
# In the case of error, -f tells curl to return nonzero, and create no output
curl -f -H "Content-Type: application/json" -d @master.json http://ghrc:8080/ghrc -o repo.tar.gz
```
