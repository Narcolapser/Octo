class LogBack:
    def __init__(self,con):
        self.con = con
        self.sftp = self.con.open_sftp()
        self.config_file = self.sftp.open("/usr/local/tomcat/webapps/uPortal/WEB-INF/classes/logback.xml")
        self.conString = self.config_file.read()
        self.conString = str(self.conString,"utf8")
##        self.conString = conString
        self.loggers = []
        i = 0
        while i < len(self.conString):
            start = self.conString.find("<logger",i)
            end = self.conString.find("</logger>",start) + len("</logger>")
            if i > end+1:
                break
            else:
                i = end+1
            print(i)
            log_string = self.conString[start:end]
            self.loggers.append(Logger(log_string))


class Logger:
    def __init__(self,val):
        self.val = val
        start = val.find('name="')+len('name="')
        self.name = val[start:val.find('"',start)]
        start = val.find('additivity="')+len('additivity="')
        self.additivity = val[start:val.find('"',start)]
        start = val.find('level="')+len('level="')
        self.level = val[start:val.find('"',start)]
        start = val.find('appender-ref ref="')+len('appender-ref ref="')
        self.appender = val[start:val.find('"',start)]

    def __str__(self):
        return '  <logger name="{0}" additivity="{1}" level="{2}">\n    <appender-ref ref="{3}"/>\n  </logger>'.format(self.name,self.additivity,self.level,self.appender)

def recursiveParse(val):
    tag_opening = val.find("<")
    if val[tag_opening:tag_opening+4] == "<!--":
        print("comment!")

example_val = """  <appender name="PORTAL" class="ch.qos.logback.core.rolling.RollingFileAppender">
    <!--See http://logback.qos.ch/manual/appenders.html#RollingFileAppender-->
    <!--and http://logback.qos.ch/manual/appenders.html#TimeBasedRollingPolicy-->
    <!--for further documentation-->
    <File>${catalina.base}/logs/portal/portal.log</File>
    <encoder>
      <pattern>%-5level [%thread] %logger{36} %d{ISO8601} - %msg%n</pattern>
    </encoder>
    <rollingPolicy class="ch.qos.logback.core.rolling.TimeBasedRollingPolicy">
      <fileNamePattern>${catalina.base}/logs/portal/portal.log.%d{yyyy-MM-dd}</fileNamePattern>
    </rollingPolicy>
  </appender>
"""

com_val = " <!-- blarg! -->"

logger_val = """
  <root level="INFO">
    <appender-ref ref="PORTAL"/>
  </root>

  <!-- Log use of the identity and attribute swapper -->
  <logger name="org.jasig.portal.portlets.swapper" additivity="false" level="INFO">
    <appender-ref ref="SWAPPER"/>
  </logger>

  <!--  Portal Event aggregation -->
  <logger name="org.jasig.portal.events" additivity="false" level="INFO">
    <appender-ref ref="EVENT"/>
  </logger>

  <!--  Portal Tin Can Events -->
  <logger name="org.jasig.portal.events.tincan.providers.LogEventTinCanAPIProvider" additivity="false" level="DEBUG">
    <appender-ref ref="TINCAN"/>
  </logger>
"""

recursiveParse(com_val)
