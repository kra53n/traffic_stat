# Traffic stat

Show statistic of proxy usage provided by 3x-ui panel in telegram.

![Statistic figure demonstration](demo.jpg)

## Usage

```
cd /root
git clone https://github.com/kra53n/traffic_stat
./setup.sh
```

## Structure

Project written in ***`Go`*** and ***`Python`***.

- ***`Go`*** - collects data from 3x-ui panel and write result to `stat.db`
- ***`Python`*** - run telegram bot and read `stat.db` when bot's users would like to get statistics.