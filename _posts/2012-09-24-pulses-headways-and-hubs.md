---
author: "mboos"
title: "Pulses, Headways, and Hubs"
date: "2012-09-24"
categories: 
  - "buses"
  - "transit"
tags: 
  - "frequent-service-networks"
  - "maps"
  - "networks"
  - "open-data"
  - "scheduling"
---

I live on Queen Street, about a 10 minute walk from Charles Street terminal. It’s a 3 minute bus ride though, and the stop outside my building is served by four different routes coming in and out of the terminal. In theory, based on the number of buses passing through each hour, you would expect an average wait of 3.5 minutes (up to 7 minutes) making the bus competitive with walking if I’m in a hurry or the weather is poor.

However, this is not the case. You can often see two or three buses coming one after another down Queen, which means there are up to 16 minutes of no scheduled service at times. We should expect 6.5 minutes of delay based on the number of buses, making taking the bus marginally faster on average. But because of the variations in bus headways, it takes almost twice as long as walking at worst. I can't simply step out my door and know whether walking or taking the bus at any given time would be faster. Clearly, the bus schedule is not very optimal for wait times near my home. If the departure times between buses travelling to Charles Street were equally spaced, rather than all arriving at once, the bus network could be made more efficient and predictable, for the same amount of service and expense.<!--more-->

#### The “cut the waits” challenge

I decided to investigate a little further, to see if there were other areas of Waterloo Region where this was a problem. My criterion for 'sub-optimal' scheduling is that the maximum wait time between successive buses at a stop is higher than if those same buses were evenly spaced in the schedule. Thankfully, the Region provides its [transit schedule as open data](https://www.regionofwaterloo.ca/en/regionalGovernment/GRT_GTFSdata.asp). Using this data, I created a map of inefficient scheduling from a user’s perspective:

\[caption id="" align="aligncenter" width="546" caption="Sub-optimal bus wait times in Waterloo Region. Click map for interactive version."\][![Click map for interactive version](/images/Screen-shot-2012-08-22-at-9.35.05-PM.png)](https://real.uwaterloo.ca/~mboos/wp-content/uploads/heatmap/heatmap.php?map=longestwait&max=20)\[/caption\]

The map shows the discrepancy between the worst wait time at a stop and what the wait time would be if buses were evenly spaced. The longest extra waiting time (shown in red) is more than 17 minutes, which tends to be in areas where there are multiple routes at different frequencies.

The suburbs perform surprisingly well in this map compared to the cores. Suburban stops tend to be served by only a single route, and while infrequent, they’re generally scheduled with consistent headways. Transit hubs have many routes going in and out of them, and have more potential for suboptimal scheduling. (There’s a reason for why they’re scheduled the way they are, but we’ll get to that below.) There's some correlation between sub-optimal wait times and bus frequency, because that's where buses of different schedules overlap.

While a 'perfect' schedule with no local sub-optimalities may be impossible to achieve, it's clear there are many places where shifting certain routes by a few minutes would help even out the schedule.

#### Making the connection

Why do the bus schedules have so much sub-optimal waiting for users? Hubs and pulses.

Hubs are places where many buses meet and from which they radiate out like spokes. They make good sense in low-density areas with centres of interest, which is what our Region has been like in the past. (Though they also compound the already convoluted nature of our road network!)  This is why you have a lot of different routes covering the same streets - there are only so many streets that can be driven into a given hub, and dedicating particular streets saves on bus shelters and intersection design. With frequent services like the 7 and 200 iXpress, we are building a 'spine' style transit system, but unfortunately we aren't finishing the job with 'ribs' when we leave this hub-and-spoke system intact. Current cross-corridor transit leaves something to be desired.

Pulses are what transit agencies do to try to improve connections for infrequent services. It's part of why you see buses idle for several minutes at Charles Street Station and then all leave one after another. They all try to arrive, wait, and then leave around the same time so you can make your transfer. This is great in theory, though less so in practice. If your first bus is delayed a few minutes (as often happens), there are no buses for you to take until the next pulse, which here generally means waiting another 30 minutes (or an hour in the evenings).

The combination of hubs and pulses create this bunching of buses I witness from my window on Queen Street. The good news is, it doesn't have to stay this way. The Light Rail line will strengthen our spine system, and additional iXpress services will begin to form the ribs. If the Region can accelerate its implementation of more frequent service bus lines, pulsing could either be adapted to match rapid transit stops, or deemed unnecessary as the next train is only a few minutes away. I really hope we don't retain our old GRT scheduling quirks as this new network emerges. GRT and Waterloo Region are slowly moving beyond the small-town thinking of pulses and hubs towards building a modern high-frequency urban transit network, but they could be doing it faster.

_Mike Boos is a member of the Tri-cities Transport Action Group. [Visit his website](https://real.uwaterloo.ca/~mboos/?p=797) to learn more about how the map in this post was created._
