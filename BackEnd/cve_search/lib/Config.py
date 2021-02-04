#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Config reader to read the configuration file
#
# Software is free software released under the "GNU Affero General Public License v3.0"
#
# Copyright (c) 2013-2018  Alexandre Dulaunoy - a@foo.be
# Copyright (c) 2014-2018  Pieter-Jan Moreels - pieterjan.moreels@gmail.com

import bz2
import configparser
import datetime
import gzip
import os
import re
import ssl
import urllib.parse
import urllib.request as req
import zipfile
from io import BytesIO

import pymongo
import redis

runPath = os.path.dirname(os.path.realpath(__file__))


class Configuration:
    ConfigParser = configparser.ConfigParser()
    ConfigParser.read(
        [
            os.path.join(runPath, "../etc/configuration.ini"),
            os.path.join(runPath, "../etc/sources.ini"),
        ]
    )
    default = {
        "redisHost": "localhost",
        "redisPort": 6379,
        "redisQ": 9,
        "redisVendorDB": 10,
        "redisNotificationsDB": 11,
        "redisRefDB": 12,
        "redisPass": None,
        "mongoHost": "localhost",
        "mongoPort": 27017,
        "mongoDB": "cvedb",
        "mongoUsername": "",
        "mongoPassword": "",
        "DatabasePluginName": "mongodb",
        "flaskHost": "127.0.0.1",
        "flaskPort": 5000,
        "flaskDebug": True,
        "pageLength": 50,
        "loginRequired": False,
        "listLogin": True,
        "ssl": False,
        "sslCertificate": "./ssl/cve-search.crt",
        "sslKey": "./ssl/cve-search.crt",
        "CVEStartYear": 2002,
        "logging": True,
        "logfile": "./log/cve-search.log",
        "maxLogSize": "100MB",
        "backlog": 5,
        "Indexdir": "./indexdir",
        "updatelogfile": "./log/update_populate.log",
        "Tmpdir": "./tmp",
        "http_proxy": "",
        "http_ignore_certs": False,
        "plugin_load": "./etc/plugins.txt",
        "plugin_config": "./etc/plugins.ini",
        "auth_load": "./etc/auth.txt",
        "WebInterface": "Full",  # defaults to Full; choices are 'Full' or 'Minimal'
    }

    sources = {
        "cve": "https://nvd.nist.gov/feeds/json/cve/1.1/",
        "cpe": "https://nvd.nist.gov/feeds/json/cpematch/1.0/nvdcpematch-1.0.json.zip",
        "cwe": "https://cwe.mitre.org/data/xml/cwec_v4.3.xml.zip",
        "capec": "https://capec.mitre.org/data/xml/capec_v3.4.xml",
        "via4": "https://www.cve-search.org/feeds/via4.json",
        "includecve": True,
        "includecapec": True,
        "includemsbulletin": True,
        "includecpe": True,
        "includecwe": True,
        "includevia4": True,
    }

    @classmethod
    def reloadConfiguration(cls):
        cls.ConfigParser.clear()
        return cls.ConfigParser.read(
            [
                os.path.join(runPath, "../etc/configuration.ini"),
                os.path.join(runPath, "../etc/sources.ini"),
            ]
        )

    @classmethod
    def readSetting(cls, section, item, default):
        result = default
        try:
            if type(default) == bool:
                result = cls.ConfigParser.getboolean(section, item)
            elif type(default) == int:
                result = cls.ConfigParser.getint(section, item)
            else:
                result = cls.ConfigParser.get(section, item)
        except:
            pass
        return result

    @classmethod
    def getWebInterface(cls):
        return cls.readSetting("Webserver", "WebInterface", cls.default["WebInterface"])

    # Mongo
    @classmethod
    def getMongoDB(cls):
        return cls.readSetting("Database", "DB", cls.default["mongoDB"])

    @classmethod
    def getMongoConnection(cls):
        mongoHost = cls.readSetting("Database", "Host", cls.default["mongoHost"])
        mongoPort = cls.readSetting("Database", "Port", cls.default["mongoPort"])
        mongoDB = cls.getMongoDB()
        mongoUsername = urllib.parse.quote(
            cls.readSetting("Database", "Username", cls.default["mongoUsername"])
        )
        mongoPassword = urllib.parse.quote(
            cls.readSetting("Database", "Password", cls.default["mongoPassword"])
        )
        if mongoUsername and mongoPassword:
            mongoURI = "mongodb://{username}:{password}@{host}:{port}/{db}".format(
                username=mongoUsername,
                password=mongoPassword,
                host=mongoHost,
                port=mongoPort,
                db=mongoDB,
            )
        else:
            mongoURI = "mongodb://{host}:{port}/{db}".format(
                host=mongoHost, port=mongoPort, db=mongoDB
            )
        # jdt_NOTE: now correctly catches exceptions due to changes in pymongo 2.9 or later
        # jdt_NOTE: https://api.mongodb.com/python/current/migrate-to-pymongo3.html#mongoclient-connects-asynchronously
        connect = pymongo.MongoClient(mongoURI, connect=False)
        return connect[mongoDB]

    @classmethod
    def toPath(cls, path):
        return path if os.path.isabs(path) else os.path.join(runPath, "..", path)

    # Redis
    @classmethod
    def getRedisHost(cls):
        return cls.readSetting("Redis", "Host", cls.default["redisHost"])

    @classmethod
    def getRedisPort(cls):
        return cls.readSetting("Redis", "Port", cls.default["redisPort"])

    @classmethod
    def getRedisVendorConnection(cls):
        redisHost = cls.getRedisHost()
        redisPort = cls.getRedisPort()
        redisDB = cls.readSetting("Redis", "VendorsDB", cls.default["redisVendorDB"])
        redisPass = cls.readSetting("Redis", "Password", cls.default["redisPass"])
        return redis.StrictRedis(
            host=redisHost,
            port=redisPort,
            db=redisDB,
            password=redisPass,
            charset="utf-8",
            decode_responses=True,
        )

    @classmethod
    def getRedisTokenConnection(cls):
        redisHost = cls.getRedisHost()
        redisPort = cls.getRedisPort()
        redisPass = cls.readSetting("Redis", "Password", cls.default["redisPass"])
        return redis.StrictRedis(
            host=redisHost,
            port=redisPort,
            db=8,
            password=redisPass,
            charset="utf-8",
            decode_responses=True,
        )

    @classmethod
    def getRedisNotificationsConnection(cls):
        redisHost = cls.getRedisHost()
        redisPort = cls.getRedisPort()
        redisDB = cls.readSetting(
            "Redis", "NotificationsDB", cls.default["redisNotificationsDB"]
        )
        redisPass = cls.readSetting("Redis", "Password", cls.default["redisPass"])
        return redis.StrictRedis(
            host=redisHost,
            port=redisPort,
            db=redisDB,
            password=redisPass,
            charset="utf-8",
            decode_responses=True,
        )

    @classmethod
    def getRedisRefConnection(cls):
        redisHost = cls.getRedisHost()
        redisPort = cls.getRedisPort()
        redisDB = cls.readSetting("Redis", "RefDB", cls.default["redisRefDB"])
        redisPass = cls.readSetting("Redis", "Password", cls.default["redisPass"])
        return redis.StrictRedis(
            host=redisHost,
            port=redisPort,
            db=redisDB,
            password=redisPass,
            charset="utf-8",
            decode_responses=True,
        )

    @classmethod
    def getRedisQConnection(cls):
        redisHost = cls.getRedisHost()
        redisPort = cls.getRedisPort()
        redisDB = cls.readSetting("Redis", "redisQ", cls.default["redisQ"])
        redisPass = cls.readSetting("Redis", "Password", cls.default["redisPass"])
        return redis.StrictRedis(
            host=redisHost,
            port=redisPort,
            db=redisDB,
            password=redisPass,
            charset="utf-8",
            decode_responses=True,
        )

    # Flask
    @classmethod
    def getFlaskHost(cls):
        return cls.readSetting("Webserver", "Host", cls.default["flaskHost"])

    @classmethod
    def getFlaskPort(cls):
        return cls.readSetting("Webserver", "Port", cls.default["flaskPort"])

    @classmethod
    def getFlaskDebug(cls):
        return cls.readSetting("Webserver", "Debug", cls.default["flaskDebug"])

    # Webserver
    @classmethod
    def getPageLength(cls):
        return cls.readSetting("Webserver", "PageLength", cls.default["pageLength"])

    # Authentication
    @classmethod
    def loginRequired(cls):
        return cls.readSetting(
            "Webserver", "LoginRequired", cls.default["loginRequired"]
        )

    @classmethod
    def listLoginRequired(cls):
        return cls.readSetting(
            "Webserver", "ListLoginRequired", cls.default["listLogin"]
        )

    @classmethod
    def getAuthLoadSettings(cls):
        return cls.toPath(
            cls.readSetting("Webserver", "authSettings", cls.default["auth_load"])
        )

    # SSL
    @classmethod
    def useSSL(cls):
        return cls.readSetting("Webserver", "SSL", cls.default["ssl"])

    @classmethod
    def getSSLCert(cls):
        return cls.toPath(
            cls.readSetting("Webserver", "Certificate", cls.default["sslCertificate"])
        )

    @classmethod
    def getSSLKey(cls):
        return cls.toPath(cls.readSetting("Webserver", "Key", cls.default["sslKey"]))

    # CVE
    @classmethod
    def getCVEStartYear(cls):
        YEAR_CVE_BEGAN = 2002
        next_year = datetime.datetime.now().year + 1
        start_year = cls.readSetting("CVE", "StartYear", cls.default["CVEStartYear"])
        if start_year < YEAR_CVE_BEGAN or start_year > next_year:
            print(
                "The year %i is not a valid year.\ndefault year %i will be used."
                % (start_year, cls.default["CVEStartYear"])
            )
            start_year = cls.default["CVEStartYear"]
        return start_year

    # Logging
    @classmethod
    def getLogfile(cls):
        return cls.toPath(cls.readSetting("Logging", "Logfile", cls.default["logfile"]))

    @classmethod
    def getUpdateLogFile(cls):
        return cls.toPath(
            cls.readSetting("Logging", "Updatelogfile", cls.default["updatelogfile"])
        )

    @classmethod
    def getLogging(cls):
        return cls.readSetting("Logging", "Logging", cls.default["logging"])

    @classmethod
    def getMaxLogSize(cls):
        size = cls.readSetting("Logging", "MaxSize", cls.default["maxLogSize"])
        split = re.findall("\d+|\D+", size)
        multipliers = {"KB": 1024, "MB": 1024 * 1024, "GB": 1024 * 1024 * 1024}
        if len(split) == 2:
            base = int(split[0])
            unit = split[1].strip().upper()
            return base * multipliers.get(unit, 1024 * 1024)
        # if size is not a correctly defined set it to 100MB
        else:
            return 100 * 1024 * 1024

    @classmethod
    def getBacklog(cls):
        return cls.readSetting("Logging", "Backlog", cls.default["backlog"])

    # Indexing
    @classmethod
    def getTmpdir(cls):
        return cls.toPath(cls.readSetting("dbmgt", "Tmpdir", cls.default["Tmpdir"]))

    # Indexing
    @classmethod
    def getIndexdir(cls):
        return cls.toPath(
            cls.readSetting("FulltextIndex", "Indexdir", cls.default["Indexdir"])
        )

    # Http Proxy
    @classmethod
    def getProxy(cls):
        return cls.readSetting("Proxy", "http", cls.default["http_proxy"])

    @classmethod
    def ignoreCerts(cls):
        return cls.readSetting("Proxy", "IgnoreCerts", cls.default["http_ignore_certs"])

    @classmethod
    def getFile(cls, getfile, unpack=True):
        if cls.getProxy():
            proxy = req.ProxyHandler({"http": cls.getProxy(), "https": cls.getProxy()})
            auth = req.HTTPBasicAuthHandler()
            opener = req.build_opener(proxy, auth, req.HTTPHandler)
            req.install_opener(opener)
        if cls.ignoreCerts():
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            opener = req.build_opener(urllib.request.HTTPSHandler(context=ctx))
            req.install_opener(opener)

        response = req.urlopen(getfile)
        data = response
        # TODO: if data == text/plain; charset=utf-8, read and decode
        if unpack:
            if "gzip" in response.info().get("Content-Type"):
                buf = BytesIO(response.read())
                data = gzip.GzipFile(fileobj=buf)
            elif "bzip2" in response.info().get("Content-Type"):
                data = BytesIO(bz2.decompress(response.read()))
            elif "zip" in response.info().get("Content-Type"):
                fzip = zipfile.ZipFile(BytesIO(response.read()), "r")
                if len(fzip.namelist()) > 0:
                    data = BytesIO(fzip.read(fzip.namelist()[0]))
        return (data, response)

    # Feeds
    @classmethod
    def getFeedData(cls, source, unpack=True):
        source = cls.getFeedURL(source)
        return cls.getFile(source, unpack) if source else None

    @classmethod
    def getFeedURL(cls, source):
        cls.reloadConfiguration()
        return cls.readSetting("Sources", source, cls.sources.get(source, ""))

    @classmethod
    def includesFeed(cls, feed):
        return cls.readSetting(
            "EnabledFeeds", feed, cls.sources.get("include" + feed, False)
        )

    # Plugins
    @classmethod
    def getPluginLoadSettings(cls):
        return cls.toPath(
            cls.readSetting("Plugins", "loadSettings", cls.default["plugin_load"])
        )

    @classmethod
    def getPluginsettings(cls):
        return cls.toPath(
            cls.readSetting("Plugins", "pluginSettings", cls.default["plugin_config"])
        )


class ConfigReader:
    def __init__(self, file):
        self.ConfigParser = configparser.ConfigParser()
        self.ConfigParser.read(file)

    def read(self, section, item, default):
        result = default
        try:
            if type(default) == bool:
                result = self.ConfigParser.getboolean(section, item)
            elif type(default) == int:
                result = self.ConfigParser.getint(section, item)
            else:
                result = self.ConfigParser.get(section, item)
        except:
            pass
        return result
