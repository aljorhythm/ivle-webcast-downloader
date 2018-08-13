/** Main */
const fs = require("fs");

var getWebcastsPage = function(webcastsPage) {
  const webcastsUrl = webcastsPage.url;
  const moduleTitle = webcastsPage.module;

  const getLinks = function(selector) {
    const inner = function(selector) {
      var links = document.getElementsByTagName(selector);
      links = Array.prototype.map.call(links, function(link) {
        return link.getAttribute("href");
      });
      return links;
    };
    if (selector) {
      return function() {
        inner(selector);
      };
    } else {
      return inner("a");
    }
  };

  const casper = require("casper").create({
    verbose: true,
    logLevel: "log",
    pageSettings: {
      webSecurityEnabled: false
    }
  });

  casper.on("remote.message", function(resource) {
    this.echo(resource);
  });

  casper.userAgent(config.userAgent);

  casper.start(webcastsUrl, {
    pageSettings: {
      loadImages: false, // The WebPage instance used by Casper will
      loadPlugins: false // use these settings
    }
  });

  casper.then(function() {
    this.echo("Loggin In", "INFO");
    this.echo(this.getCurrentUrl(), this.getTitle(), "INFO");
    this.fillSelectors(
      "form#aspnetForm",
      {
        "input[type=text]": config.user,
        "input[type=password]": config.password
      },
      false
    );

    this.click("button[type=submit]");

    this.waitFor(function check() {
      const failedLogin = this.exists(".alert-danger");
      const loginPrompt = this.exists(".login-wrapper");
      return this.exists(".alert-danger") || !loginPrompt;
    });
  });

  casper.then(function() {
    var failedLogin = this.exists(".alert-danger");
    if (failedLogin) {
      this.echo(this.getHTML(".alert-danger span"), "ERROR");
      this.echo("Failed Login", "ERROR");
      return;
    }
    this.echo(this.getCurrentUrl() + " " + this.getTitle(), "INFO");

    const links = this.evaluate(function() {
      const rows = document.querySelectorAll("body div .panel table tr");
      const links = [];
      const max = 6 || rows.length;
      for (var i = 1; i < max; i++) {
        // for (var i = 1; i < 10; i++) {
        const row = rows[i];
        const mp4Cell = row.cells[1];
        const titleCell = row.cells[2];
        if (mp4Cell) {
          const a = mp4Cell.children[2];
          if (a) {
            a.click();
          }
          if (a && a.id) {
            const titleA = titleCell.children[2];
            links.push({
              // selector: "#" + a.id,
              title: titleA.text
            });
          }
        }
      }
      return links;
    });

    this.echo(this.popups.length + " Popups, " + moduleTitle, "INFO");

    function getSplashScreenVisibility() {
      return document.querySelector("#splashScreen").style.display != "none";
    }

    for (var i = 0; i < this.popups.length; i++) {
      this.withPopup(i, function() {
        this.echo("Scraping popup: " + this.getTitle(), "INFO");
        this.waitFor(
          function() {
            return (
              this.exists("#splashScreen img") &&
              this.evaluate(getSplashScreenVisibility)
            );
          },
          function() {
            this.echo(
              "SPLASHSCREEN EXISTS, Scraping Video URL " +
                this.evaluate(getSplashScreenVisibility),
              "INFO"
            );

            const objectStr =
              "a = {" +
              this.getHTML().match(/"VideoUrl":"https:.*videoPodcast"/) +
              "}";
            const videoUrl = eval(objectStr).VideoUrl;
            const webcastsDirectory = ""; //"webcasts/";
            const webcastTitle = this.getTitle();
            const outputFileName =
              webcastsDirectory + moduleTitle + " - " + webcastTitle + ".mp4";
            if (fs.isFile(outputFileName)) {
              this.echo(outputFileName + " already exists", "INFO");
            } else {
              this.echo(
                "Downloading " + videoUrl + " as " + outputFileName,
                "INFO"
              );
              this.download(videoUrl, outputFileName);
            }
          },
          function() {
            this.echo("Splash screen NOT FOUND", "ERROR");
          },
          10000
        );
      });
    }
  });

  return casper;
};

const configFilename = "config.json";
config = require(configFilename);

for (var i = 0; i < config.moduleWebcastPages.length; i++) {
  const webcastsPage = config.moduleWebcastPages[i];
  getWebcastsPage(webcastsPage).run();
}
