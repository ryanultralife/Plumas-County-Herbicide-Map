#!/usr/bin/env python3
"""Tehama County operator roster -> data/incoming/2026-09/tehama-2020-2026.csv

Source: 'SprayMap California PRA data_redacted.xlsx' (County of Tehama via County
Counsel, Prentice Long PC, 2026-08-12; re-sent by the Tehama Ag Department
2026-09-14). A full CalAgPermits 'Permits, Sites and Commodities' export,
38,611 site rows across 54 columns. The county redacted personal contact
information (phone, email, mailing detail) under Gov. Code 7922.000; operator
and agent names are retained.

Reduced here to one row per permit number (latest permit year), which is all the
name enricher needs: right(GROWER_ID, 7) == permit number. Home-county permits
from other counties (04 Butte, 11 Glenn, 45 Shasta, 51 Sutter, 58 Yuba, ...) are
kept - they are operators working Tehama ground and their GROWER_IDs carry the
same 7-digit suffix.

Three rows dropped on purpose: 1234567 'Schools, Daycares, Sensitive sites'
(a placeholder), 5209999 'Tom Moss-test' and 5299999 'JOE TEHAMA' (test permits).

The xlsx itself is not committed (data/incoming/*/ raw files are gitignored);
it lives in the spraymapca inbox thread 'PRA Request received August 3, 2026'.
"""
import csv, io, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tehama-2020-2026.csv")

ROWS = """
0400098 | RMP | Patane Farms, Farming Group LLC | Gino Patane
0400403 | RMP | Rajinder Chohan | George Chohan
0400420 | RMP | McGowan Inc. | Henry McGowan
0400433 | RMP | Bob & Susan Vanella |
0400446 | RMP | Wendell Stephens |
0400565 | RMP | Joe Ernandes |
0400983 | RMP | Capay Farms Inc. | John Kraus
0401012 | RMP | Ernest Hanson |
0401654 | RMP | Great Northern Farm Management | Marc Breckenridge
0403351 | RMP | Steve Bickley | Bickley, Steve
0403679 | RMP | Justin Mendonca | Jamee Mendonca
0403714 | RMP | R & G Orchards | Richard Horn
0403745 | RMP | Jose Luis Jauregui |
0406202 | RMP | Hardeep S. Dhadli |
0407234 | RMP | California Olive Ranch #3 | David Magana
0600111 | RMP | Peterson Ranch | Bob Harper
1100020 | RMP | Mike Chambers |
1100029 | RMP | P5 Farms | Nick Perez
1100055 | RMP | Brandon Chapla | Joshua Peterson
1100056 | RMP | Knight Farms | Craig Knight
1100083 | RMP | Jared Burreson |
1100128 | RMP | Richard Conte |
1100133 | RMP | Jim Baugher |
1100154 | Op-Id | Sycamore Properties Inc. | Navid Khan
1100336 | RMP | Benchmark Farm Management | John Campbell
1100352 | RMP | Mike Schager |
1100359 | RMP | Weber Ranch | James Weber
1100448 | RMP | Damien Rush | Damien Rush
1100467 | RMP | Jorge & Luz Sanchez | Luz Sanchez
1100475 | RMP | Red Bluff Farms | Mike Perry
1100554 | RMP | John Zuppan |
1100685 | RMP | Juan Carrillo | JC Farm Services, Inc.
1100692 | RMP | Edward Sousa |
1100770 | RMP | Jon Swaner |
1100798 | RMP | Sacramento Nat'l Wildlife Refuge | Tim Arendt
1100803 | RMP | Tehama Colusa Canal Authority | Jacob Hampton
1100894 | RMP | Caleb Unruh |
1101197 | RMP | The Nature Conservancy | Jose Ojeda
110759 | RMP | Chris Taylor |
1501507 | Op-Id | C. Loewen Ag LLC | Cyrus Loewen
3401939 | Op-Id | Lucky Janda |
4500052 | RMP | Sierra Pacific Industries-Stirling Dist. | Jonathan Freitas
4500064 | Op-Id | Nor-Cal Trees Inc. | Rick Sabanovich
4500195 | Op-Id | Franklin Logging | John Copsey
4500412 | RMP | Mel Hoy |
4902553 | RMP | Mulehead Growers | Brian Birt
491160 | RMP | Atwood Ranch | Christine Prince
5100405 | RMP | Raminder Bains | Raminder Bains
5101334 | RMP | Cornerstone Properties | Rikki Bhatti
5104066 | RMP | Kulwinder Lally |
5104237 | Op-Id | Sanjiv Midha |
5200004 | RMP | Pacific Farms & Orchards Inc. | Brendon Flynn
5200006 | Op-Id | Steve Vadney |
5200009 | Op-Id | Maria & Roque Lozano |
5200014 | RMP | Curtis Avrit |
5200016 | RMP | Gary Rumiano | RUMIANO,GARY
5200017 | Op-Id | Laurel DeClerk |
5200019 | RMP | Haleakala Ranch, LLC. | Rose Crain
5200020 | RMP | HD Coelho | HD Coelho
5200022 | RMP | Vina Orchards Inc. | John Edson
5200023 | RMP | Wesley M. Williams |
5200027 | RMP | Tehama Angus Ranch | Kevin Davies
5200028 | RMP | James Bingham |
5200029 | RMP | Crain Walnut Shelling Inc. | Charles R Crain Jr
5200030 | RMP | Eco-Shell | Jake Brazie
5200031 | RMP | Mike Foley |
5200032 | RMP | Crain Orchards | Kevin Gough
5200034 | RMP | David Wohletz |
5200039 | RMP | Long & Long Orchards | Greg Long
5200041 | Op-Id | Abbey Ranch Inc. | Francis Pham
5200043 | RMP | Golden Valley Farms | Fred Spanfelner
5200044 | RMP | Edwards Ranch/JT Farms | Tyler Christensen
5200051 | RMP | Lassen Vina Ranch | Mike Bolen
5200056 | RMP | Brian Walker |
5200059 | Op-Id | Eliseo Ramirez |
5200063 | RMP | Maywood Farms | Robert Steinacher
5200070 | Op-Id | Marcelino Robles |
5200073 | Op-Id | John Corn |
5200074 | Op-Id | Allan Fleming |
5200077 | RMP | Irene Woodward |
5200078 | RMP | JM Farms | Marcus Lowen
5200079 | RMP | Lindauer River Ranch | Warren Hicks
5200081 | RMP | Deseret of California | Rob Smith
5200082 | RMP | David Lester |
5200084 | RMP | Jim Wilson |
5200086 | RMP | Crane Mills Forestry | Ty C. Fahey
5200089 | RMP | Edward Redamonti |
5200092 | RMP | Kent Kohler | Dorea Orchards
5200105 | RMP | Roger Penner | Roger Penner
5200106 | RMP | K-2L-M/Dutro Farms | Mark Dutro
5200108 | RMP | Ronald Whiteley |
5200113 | RMP | Mathieu Esteve |
5200120 | RMP | Brandt Orchards | James Brandt
5200121 | RMP | Harman Ranch | Russ Harman
5200122 | RMP | Pete Neves |
5200130 | RMP | Andersen & Sons Ranch | Franklin K. Andersen
5200132 | RMP | Matt Terry |
5200133 | Op-Id | Librada Reyes |
5200136 | RMP | Greg Jones |
5200143 | Op-Id | Doug White | Jeff White
5200152 | RMP | Pat Maguire |
5200163 | Op-Id | Darl Smith |
5200164 | Op-Id | Corning Water District | Moises Alvarado
5200166 | RMP | Driscoll Strawberry Assoc. | Shane Overton
5200170 | RMP | Larry Kunau |
5200177 | Op-Id | Gifford Tallmadge |
5200184 | RMP | Scott Murphy |
5200185 | RMP | Cody McCoy |
5200186 | Op-Id | Ohm Ranch | John Ohm
5200196 | Op-Id | Deborah Gregorio |
5200205 | Op-Id | Ignacio Meza | Hilda Meza
5200209 | RMP | Crown Nursery | Carl Anberg
5200211 | RMP | Chris Rosauer |
5200219 | RMP | Corning Orchards | Nicholas McGowan
5200222 | RMP | Norm Zimmerman |
5200226 | Op-Id | Russell Heitkam |
5200230 | RMP | Sutfin Land and Livestock | Arthur Sutfin
5200232 | RMP | Frank Endres |
5200241 | RMP | Darlene Olson | James Olson
5200242 | RMP | Eric Willard |
5200246 | Op-Id | Bruce Perkin |
5200249 | RMP | Robert Kerstiens Jr |
5200258 | RMP | Brian Ross |
5200294 | RMP | Doris Koshman |
5200302 | Op-Id | Alain Teutschmann |
5200315 | RMP | Sunsweet Growers | Joseph Ackley
5200317 | Op-Id | Dorothy Lipari |
5200319 | RMP | Crain Farming Operations, LLC. | Dustin Crain
5200323 | RMP | California Walnut Co. | Greg Gilchrist
5200327 | RMP | Brian Uchytil | Brian Uchytil
5200331 | RMP | Merton S McFall |
5200342 | RMP | Ryan Patrick | Ryan Patrick
5200351 | Op-Id | Steve Zimmerman |
5200353 | RMP | Tom Darrow | Tom Darrow
5200354 | RMP | Genoa Farms | Scott Meinberg
5200355 | RMP | Curt Martin |
5200357 | RMP | Steve Richardson | Richardson,Steve
5200359 | Op-Id | Gerber-Las Flores CSD | Emde, Shane
5200361 | Op-Id | Linda Ezzat | Zamil Ezzat/Triple Z Ranch
5200363 | Op-Id | Ted Demos |
5200366 | RMP | Diamond G Corporation | Larry Galper
5200372 | Op-Id | Luis Tapia |
5200376 | RMP | Heritage Nut Farms | Steve Slacks
5200379 | Op-Id | Dempsey's Apiary | Daniel Dempsey
5200393 | RMP | Eduardo M. Curiel |
5200394 | RMP | Doyle Ranch Inc. | Bryce Biswell
5200399 | Op-Id | Raul Fregozo |
5200401 | Op-Id | Jorge Lozano |
5200402 | Op-Id | Jose Luiz Lozano | Jose & Pedro Lozano
5200405 | RMP | John Christenson |
5200419 | Op-Id | Jose Mendez |
5200424 | Op-Id | Carlos Calderon |
5200430 | Op-Id | Emmanuel Chavez |
5200432 | RMP | Antonio Rosiles |
5200434 | RMP | Frank Passantino |
5200437 | Op-Id | Gerardo Leal |
5200439 | Op-Id | Roger Matz |
5200440 | Op-Id | Marciano Curiel | Curiel,Jose
5200442 | Op-Id | Jose Miranda | Alex Miranda
5200443 | RMP | Dan & Rose Kemp |
5200444 | Op-Id | Reynaldo Valencia-Zepeda | Reynaldo Valencia-Zepeda
5200451 | RMP | Jerry Oliver |
5200461 | RMP | Tom Jones |
5200463 | RMP | Elias Villegas | Moises Villegas
5200464 | RMP | Charles Johnson | Chad Johnson
5200468 | Op-Id | Epifanio Ruiz |
5200473 | Op-Id | Alan Honore | Western Chemical Applicators
5200476 | RMP | Turri Cattle LLC | Tony Turri
5200481 | RMP | Jack Moser |
5200483 | RMP | Doug Meents |
5200486 | Op-Id | Clayton Bennett |
5200488 | Op-Id | Eugenio Solorio |
5200521 | Op-Id | Exequiel & Elsa Rubio |
5200525 | Op-Id | Gary Burton |
5200543 | RMP | John Cottier |
5200544 | RMP | Ray Crawford |
5200550 | Op-Id | Bianchi Orchards |
5200554 | RMP | Joe Van Sweden |
5200559 | Op-Id | P.N. Jenkins | Craig Jenkins
5200562 | RMP | Brentwood Farms | Jen Spaletta
5200563 | Op-Id | Rick Arrowsmith |
5200566 | RMP | Richard Edsall |
5200569 | RMP | Dustin Fleming | Fleming, Dustin
5200573 | RMP | Cotton Bow Ranch | Craig Bailey
5200575 | RMP | Matt Anchordoguy |
5200579 | Op-Id | Maximino Garcia |
5200607 | RMP | Marvin Dunn |
5200608 | Op-Id | Juan M Garcia |
5200609 | RMP | Luke Alexander |
5200614 | Op-Id | Scott and Linda Patton | Scott Patton
5200615 | Op-Id | Rene Medina |
5200623 | Op-Id | Tom Wilson |
5200633 | RMP | Sandy Fee |
5200640 | RMP | Jose Mendoza |
5200650 | Op-Id | Mark & Cindi Gilles |
5200655 | RMP | JC Selvester |
5200659 | RMP | Doug Reed |
5200660 | Op-Id | Kelly Huff |
5200665 | RMP | Williams Ranch | Robert Williams
5200667 | RMP | Rocque Merlo |
5200688 | RMP | Robert Mills |
5200689 | RMP | Don Minto |
5200690 | Op-Id | Bob Crockett |
5200692 | RMP | Ron Worthley |
5200699 | RMP | Crane Mills | Brian Crane
5200708 | Op-Id | Ken Randles |
5200709 | Op-Id | CA State Parks/Wildlands | Chaye M Vail
5200712 | RMP | Hart Farms | Brian Bly
5200713 | RMP | Michael Scotella |
5200714 | RMP | Sale Family Orchard | Ryan Sale
5200715 | Op-Id | Steve Menefee |
5200717 | Op-Id | Rodrigo Vargas |
5200720 | RMP | Bruce Lindauer |
5200723 | RMP | Dave Martin | Martin, Dave
5200729 | Op-Id | Steve Dubois |
5200731 | Op-Id | David Pooler |
5200736 | RMP | FMS-FMJH | David Evers
5200745 | RMP | Byron Vance |
5200752 | Op-Id | Roy Yarbrough |
5200755 | RMP | Wayne Martin |
5200756 | Op-Id | Alger Vineyards | John Alger
5200773 | Op-Id | Steve Marriott |
5200775 | Op-Id | Herman Chen |
5200777 | Op-Id | Pete Taylor |
5200788 | RMP | Macario Figueroa |
5200791 | RMP | Ben Chambers |
5200792 | RMP | Lucky Dog Farms | Martin Spannaus
5200794 | Op-Id | German Gonzalez |
5200812 | RMP | Kevin Johnson |
5200814 | Op-Id | Demetrio Munoz |
5200815 | RMP | Vista Lakes Ranch | Ken Pilcher
5200817 | Op-Id | Chad Fambrough | Chad Fambrough
5200819 | RMP | Crain Marketing, Inc. | Ben Crain
5200824 | RMP | Gabe Martin | John Martin
5200826 | RMP | Dale Thomas |
5200833 | Op-Id | Melinda Nickler |
5200838 | RMP | Vogt's Holstein Dairies | Johnny Vogt Sr.
5200844 | RMP | Glenda Babbitt |
5200855 | Op-Id | Dharminder Janda | Dharminder Janda
5200862 | Op-Id | Steve & Cindy McClain |
5200865 | Op-Id | Adan Garcia Corona |
5200866 | Op-Id | Ronald Clark |
5200868 | RMP | Jason Quillen | Jim Quillen
5200874 | RMP | Jason Stimpel |
5200875 | Op-Id | S & F Farms | Rich Senter
5200880 | Op-Id | Roy Ekland |
5200886 | RMP | Tad Farms | Steve Dail
5200891 | RMP | Duck Pond Orchards | Greg Long
5200893 | Op-Id | Richard Greene | Herculano Farias
5200902 | RMP | BurksBarn | Darin Burks
5200903 | RMP | Steve McCarthy |
5200908 | RMP | Trent Thomas |
5200915 | RMP | Dennis Bentz |
5200918 | RMP | Bill Ridge |
5200919 | Op-Id | Nicolas Bravo |
5200920 | Op-Id | Doug & Joy Kilner |
5200922 | Op-Id | Carolyn Stokes | Carolyn Stokes
5200930 | RMP | Daniel Stewart |
5200938 | RMP | MAG Farms - Luke Alexander | Luke Alexander
5200939 | RMP | G & H Ranch | Gabe Alvarado
5200940 | RMP | JJB Farms | DC Felciano
5200941 | Op-Id | Benjamin Williams |
5200947 | RMP | Kuljit (Ken) Barns | Seth Lawrence
5200951 | Op-Id | Juan Santillan |
5200958 | Op-Id | Salvador Corona |
5200962 | RMP | Herrick Grapevines | Diego Barison
5200964 | RMP | Luke Reimers |
5200968 | Op-Id | Hank Pritchard |
5200973 | RMP | Nirmal Janda |
5200976 | Op-Id | Humberto Gonzales |
5200977 | RMP | Thomas Darlington |
5200978 | RMP | West River/Greg Long | Greg Long
5200982 | RMP | Gilchrist Properties | Greg Gilchrist
5200986 | RMP | Mary Bundy | Mary Bundy
5200987 | RMP | Mark Pritchard |
5200990 | RMP | Ron Cinquini |
5200993 | RMP | Erik & Jessica Prouty |
5200995 | Op-Id | Michael Nicholas |
5200996 | Op-Id | Efrain and Rocio Leal |
5201000 | RMP | Valley Prune | John Taylor
5201006 | RMP | Glenn Hawes |
5201011 | Op-Id | Wilcox Oaks Golf & Country Club | Cassidy Griffith
5201012 | RMP | John Rochfort |
5201014 | RMP | Hausman Orchards | Doug Hausman
5201016 | Op-Id | Los Molinos Mutual Water Co. | Bill Hardwick
5201023 | Op-Id | Judith L. Walker Trust |
5201024 | RMP | Frank Schubert |
5201026 | RMP | Sycamore Ranch | Brad Call
5201029 | RMP | John Edson | John Edson
5201031 | RMP | Tim Young |
5201033 | RMP | Kevin Hebrew | Deborah Hebrew
5201034 | RMP | Seth Lawrence |
5201037 | Op-Id | Indian Peak Vineyards |
5201038 | RMP | Thomas McDaniel | McDaniel, Carol
5201041 | RMP | Craig Arbogast |
5201043 | RMP | Triple Y Ranch | Ryan Bailey
5201046 | RMP | Curtis Eller |
5201049 | RMP | Paul Sutfin | Joshua Petersen
5201057 | Op-Id | Tehama County Courthouse | Courthouse and Grounds
5201058 | Op-Id | David Krenek |
5201065 | RMP | Juan Nerey | Pablo Nerey
5201072 | RMP | J Garcia Olive Company, LLC | Edward Garcia
5201074 | Op-Id | Edelmira Haro | Edelmira Haro
5201076 | RMP | Manpreet Sandhu |
5201079 | RMP | Mark Gwaltney/Elder Creek Orchard | Toni Gwaltney
5201080 | Op-Id | William Spaletta |
5201084 | RMP | Tim Carroll |
5201085 | Op-Id | Steve Botts |
5201087 | RMP | Berton Bertagna |
5201089 | Op-Id | Teresa Curiel | Leopoldo Curiel
5201090 | RMP | Edward Kiesel |
5201091 | Op-Id | Charles Gildea |
5201092 | RMP | Walker Creek Orchards | Jerry Montz
5201094 | RMP | Zac Mazzotta | Zac Mazzotta
5201096 | Op-Id | Larry Branham |
5201098 | Op-Id | SMKD LLC | Scott Dudley
5201102 | Op-Id | Lerose Lane |
5201104 | Op-Id | Wendell Raimer |
5201107 | Op-Id | Roy Fowler |
5201110 | RMP | Brad Taylor |
5201114 | Op-Id | Turner Ranch | Ross Turner
5201120 | RMP | Rex Wilson |
5201122 | RMP | Richard Neves |
5201132 | RMP | Matt Koball |
5201133 | Op-Id | Yvonne Ricker |
5201134 | RMP | Steve Mahoney |
5201135 | RMP | Lapant Farming Inc | Lucas Lapant
5201142 | RMP | Sierra Pacific Co. Industries | Russell Garrison
5201143 | RMP | Philip Sunseri |
5201145 | Op-Id | Ron Babb | Babb, Ron
5201148 | RMP | Jared Smith | Jared Smith
5201149 | Op-Id | Jack & Carolyn Haynes | Haynes Family Ranch
5201151 | RMP | Adam Davy |
5201158 | RMP | German Campos |
5201162 | RMP | Joseph Rider |
5201163 | Op-Id | Steve Berens | Steve Berens
5201165 | Op-Id | John Thornton | Kathy Thornton
5201168 | Op-Id | David Bennetts |
5201175 | Op-Id | Can-Am Apiaries, Inc | Brad Pankratz
5201179 | RMP | Rosalio Lopez Curiel |
5201180 | Op-Id | Joel Curiel Duenas |
5201182 | Op-Id | Colin & Sophia Swarthout |
5201184 | Op-Id | George Zimmerman |
5201185 | RMP | Kirk Jennings |
5201186 | RMP | Steve Gruenwald |
5201193 | RMP | Rolling Hills Inc | Robert Riemer
5201194 | RMP | Corning Union High School Farm/Rodgers R | Antonio Rosiles
5201199 | RMP | Uriel Castillo |
5201200 | Op-Id | Aldon Burlison |
5201202 | Op-Id | Nick Curiel |
5201204 | RMP | Tony Deniz |
5201205 | Op-Id | Long Ranch |
5201207 | RMP | Humphrey Ranch, Inc. | Bryce O'Sullivan
5201208 | RMP | Lavy Brothers | Brent Elrich
5201209 | RMP | Daved Moore |
5201210 | Op-Id | Flying T Ranch | Andrew Chrisler
5201214 | Op-Id | Tim Vanek |
5201215 | RMP | Acana Management Services | Joe Camarena
5201216 | RMP | Wade Deitz |
5201218 | Op-Id | Felipe Sanchez | Felipe Sanchez
5201222 | RMP | Mark Budke |
5201223 | RMP | Stuart Douglass |
5201224 | Op-Id | Cordell Cose |
5201227 | RMP | Justin Jourdan |
5201229 | Op-Id | Mitch Kofford | Mitch Kofford
5201230 | RMP | Salvador Chavez Jr. |
5201235 | RMP | Thiara, Ravi & Jay Farms |
5201238 | Op-Id | Reynolds | Greg Fletcher
5201239 | RMP | Febe Farm | Scott Stephens
5201241 | RMP | Marjon Enterprises | Brent Elrich
5201246 | Op-Id | Diego Guerrero |
5201248 | RMP | Mitchell Mootz |
5201255 | Op-Id | Rosalie Henderson |
5201257 | RMP | Juan Graciano |
5201258 | Op-Id | Kelsey King |
5201259 | Op-Id | Francisco Alvarado | Francisco Alvarado
5201260 | RMP | Luke Kampmann |
5201261 | Op-Id | David O'Keefe |
5201263 | Op-Id | Irineo Alvarado |
5201266 | Op-Id | California Dept of Transportation | Thomas March
5201267 | RMP | Bob Vinson |
5201271 | Op-Id | Alfredo Leal |
5201279 | Op-Id | Val Theis |
5201280 | Op-Id | Charles Orwick III Trust of 2001 | David Nipar
5201282 | RMP | Brian Berry |
5201283 | RMP | Scott Claussen |
5201285 | Op-Id | Gilbert Dilouie |
5201286 | RMP | Anuradha Chandramouli |
5201289 | Op-Id | Jorge Hernandez |
5201290 | RMP | JRT1 | Brent Elrich
5201292 | Op-Id | Julissa Garcia |
5201293 | RMP | Ryan Cumpton | Ryan Cumpton
5201295 | Op-Id | Artemio Arce | Artemio Arce
5201296 | Op-Id | Harbinder Singh Janda |
5201297 | RMP | Christopher Barajas |
5201299 | Op-Id | Raging Bull Vineyards |
5201300 | RMP | Jose Oseguera |
5201302 | RMP | Gene Gregory |
5201303 | RMP | Mike McCluskey |
5201305 | RMP | Gary Hayes |
5201309 | Op-Id | Red Bluff Cemetery District | Leland Owens
5201312 | Op-Id | Gerardo Mendoza |
5201314 | RMP | Kendel Trent |
5201315 | Op-Id | Brandi Greene |
5201318 | Op-Id | Calif. Dept. of Parks & Rec. | Ron Yocum
5201319 | Op-Id | Joey Howard |
5201320 | Op-Id | Filogonio Paz |
5201325 | RMP | Jeff Jackson |
5201326 | Op-Id | Troy Heathcote |
5201327 | RMP | Alberto Mendoza |
5201330 | Op-Id | Michael Lane |
5201332 | Op-Id | Dennis Nickell |
5201334 | RMP | Liberty Land Management | Michael Lee Smith
5201335 | Op-Id | Rigoberto Cesante |
5201336 | RMP | Bains Farming LP | Surjit Bains
5201337 | RMP | Lee Smith |
5201338 | Op-Id | Corning Cemetery District | Wendy Pauling
5201339 | RMP | International Farm Management |
5201340 | RMP | Big Hat Custom Farming | James Lefor, Will Keeney
5201341 | Op-Id | Jerad Davis |
5201342 | Op-Id | Velma Archer |
5201344 | Op-Id | Robert Thomson |
5201345 | RMP | Todd Henderson |
5201346 | Op-Id | Saxon Peters |
5201349 | RMP | CAPEX | Mathieu Esteve
5201350 | Op-Id | Western Shasta RCD | Kelli England
5201352 | Op-Id | Pete Dagorret |
5201353 | Op-Id | Mark Dunworth |
5201354 | Op-Id | John Venable |
5201355 | Op-Id | Frank Ford |
5201357 | RMP | Tom Bengard Ranch | Greg Long
5201358 | RMP | Red Bank Ranch | Donna Har
5201359 | RMP | Colby & Nicholas Anderson | Colby Anderson
5201360 | Op-Id | Valentin Alonzo |
5201363 | Op-Id | Jose Sosa |
5201365 | RMP | Jeremiah Zane |
5201367 | RMP | Englehardt Ag Services | Robert Ayala
5201370 | Op-Id | Lynch Ranch | Shannon Raker
5201374 | Op-Id | Brandon Durham |
5201375 | RMP | Michael Davis |
5201376 | Op-Id | Britt Schumacher |
5201377 | Op-Id | Burdick Ranches | Miguel Avila
5201378 | RMP | Brad Martin |
5201379 | Op-Id | Gary Strack |
5201380 | RMP | B&N Farming Inc. | Warren Gilbert
5201381 | Op-Id | Luis Jimenez |
5201382 | Op-Id | Moxley Gardens & More | Michael & Lea Ann Moxley
5201383 | RMP | Gayle Carter |
5201384 | RMP | Rutledge Farming | Tim O'Neill
5201385 | Op-Id | Donald Pitts |
5201386 | RMP | Eusebio Romero Canedo |
5201387 | Op-Id | Robbie Bianchi | Robbie Bianchi
5201390 | RMP | Sam Mudd |
5201391 | RMP | John Montz Jr. |
5201392 | RMP | Arnold Cramer |
5201393 | Op-Id | Steve Gappa |
5201394 | Op-Id | Kent Matz |
5201395 | RMP | Dulai Farms | Hardave Dulai
5201396 | RMP | Charles Gracey |
5201397 | Op-Id | Dave Santino |
5201398 | Op-Id | Sierra Pacific - Anderson | Ryan Hadley
5201399 | Op-Id | Mike Bacca |
5201400 | Op-Id | Rogelio Dominguez |
5201402 | RMP | Norman Schmidt |
5201403 | Op-Id | John Caravella |
5201404 | Op-Id | Scott Brown |
5201405 | Op-Id | John F. Larson |
5201406 | RMP | Isher Singh |
5201407 | Op-Id | JS Farm | Harpreet Gill
5201408 | Op-Id | Maria Belo | Tiburcio Belo
5201409 | RMP | Luis Muniz |
5201410 | RMP | Leland Hogan |
5201411 | RMP | Athena Ocampo |
5201412 | Op-Id | Larry Madison |
5201413 | Op-Id | James Lodin |
5201415 | RMP | Inderpaul Mahil |
5201416 | RMP | Bryan Bechthold |
5201417 | Op-Id | Epigmenio Dominguez |
5201418 | Op-Id | Ellis Farms | Roy Ellis
5201419 | Op-Id | Shasta College - Tehama Campus | Patrick McNamara
5201420 | Op-Id | Lino R. Sanchez | Lino R.Sanchez
5201421 | Op-Id | Jose Flores |
5201422 | RMP | Lassen Meadow Farms | Jeffrey Blake
5201423 | Op-Id | Ecom Hunters LLC | Lilyan Finley
5201424 | Op-Id | Terry Andersen |
5201425 | Op-Id | Trena Richards |
5201426 | Op-Id | Pedro Dominguez |
5201427 | RMP | Manuke Sandhu | Dhar Sandhu
5201428 | RMP | KYLE FRIESEN |
5201429 | Op-Id | Red Gate Ranch | Heather Austin
5201430 | RMP | Gregory Dewing |
5201431 | RMP | Richard DeRosa |
5201432 | Op-Id | Todd Brose |
5201434 | Op-Id | Peyton Pacific Properties, LLC | Lael or Gary Kirkland
5201435 | Op-Id | Novo Estates LLC | Sumanpreet Singh
5201436 | Op-Id | Thomas Wilson |
5201437 | RMP | FMS-LS2 | David Evers
5201438 | RMP | FMS-JUS | David Evers
5201439 | RMP | Duane Prestesater |
5201440 | RMP | Pete Barteles |
5201441 | RMP | G4 Farming | Warren Gilbert
5201442 | RMP | Casey Hudson |
5201443 | Op-Id | Charles Simmons | Jorge Hernandez
5201444 | Op-Id | Melchor Avila |
5201446 | RMP | Daljit Randhawa |
5201447 | Op-Id | Golden State Greenhouse | James Nolt
5201448 | RMP | Timothy Sanchez |
5201449 | Op-Id | David Arff |
5201450 | Op-Id | Vaclav Vyvoda |
5201451 | Op-Id | Tim Huckabay | Tim Huckabay
5201452 | RMP | Mark Kampmann |
5201453 | Op-Id | Walt Rogers |
5201454 | Op-Id | Jose de Jesus Garcia Cosio |
5201455 | RMP | John Patterson |
5201456 | RMP | Doug Lewis |
5201457 | Op-Id | El Vierra |
5201458 | Op-Id | Kirandeep Shahi |
5201459 | Op-Id | Stys Family Farm | Sveta & Daniel Stys
5201460 | RMP | Money Dhami |
5201461 | Op-Id | Singh Harmandeep |
5201463 | RMP | Golden State Farm LLC | Robert Zou
5201464 | RMP | Amarjit Phagura |
5201465 | RMP | Joshua Petersen |
5201466 | Op-Id | Kemp Farms |
5201467 | RMP | K-2L-M | Mark Dutro
5201468 | Op-Id | Ramon Tapia |
5201469 | RMP | Turnbull Farms | Jacob Turnbull
5201470 | Op-Id | John Runnels |
5201471 | Op-Id | Gerrie Larson |
5201472 | RMP | Vanishing Point Farms |
5201473 | Op-Id | Francisco Barajas and Gerardo Garcia |
5201474 | Op-Id | Richard Hagle |
5201475 | Op-Id | Bureau of Reclamation Nor-Cal | Benjamin Pearson
5201476 | Op-Id | Randall Saunders |
5201477 | Op-Id | Parkash Shahi |
5201478 | RMP | David Lorenzini |
5201479 | Op-Id | Jefferson Resource Co. | Cameron Miller
5201480 | Op-Id | Olive Tree Farm | Adrian Emiliano
5201481 | Op-Id | Tapia Farm Labor & Orchards | Olivia Tapia
5201482 | RMP | Dan Perea |
5201483 | RMP | Jon Villalva |
5201484 | RMP | Zamora Partners | Michael Oconnell
5201485 | RMP | Armen Khachatryan |
5201486 | Op-Id | Soledad Lopez |
5201487 | Op-Id | Mike's Land Management | Mike Marvier
5201488 | RMP | Amandeep Singh |
5201489 | RMP | Shahpur Farms | Akash Ghoman
5201490 | Op-Id | Sierra Pacific Windows | James Buckley
5201491 | Op-Id | Olive City Farm | Corey Bugenig
5201492 | Op-Id | Jose Armejo |
5201493 | RMP | Nate Oliva |
5201494 | RMP | AM Property Services -California | Timothy Sanchez
5201495 | Op-Id | Eugenio Hernandez |
5201496 | Op-Id | Steve's Tree Service | Steve Scott
5201497 | Op-Id | Pedro Lopez |
5201498 | Op-Id | Whispering Walnuts | Daniel Leavitt
5201499 | RMP | Bassi Farms | Harkiart Bassi
5201500 | RMP | Dustin Peton |
5201501 | RMP | Garry McCalla |
5201502 | Op-Id | David Court |
5201503 | Op-Id | Blue Label Apiaries | Christopher Thomas
5201504 | Op-Id | Reg Keyawa |
5201505 | RMP | Craig Love |
5201506 | RMP | Black Butte Bison Ranch | Thomas Frankovich
5201508 | Op-Id | Battle Creek Meadows Ranch, Inc. | Phred Starkweather
5201509 | Op-Id | Cisneros and Sons Honey Bees | David Cisneros
5201510 | RMP | Badyal Farm Family | Ashvir Singh
5201511 | Op-Id | Paul Korhuniak | Edward Fredrickson
5201512 | Op-Id | Karen Palmer |
5201513 | Op-Id | Arce Bee's Apiaries | Adan Arce
5201514 | Op-Id | Janell Kelley |
5201515 | RMP | Keeling Farms | Kody Keeling
5201516 | Op-Id | Jason Abel |
5201517 | Op-Id | Lisa Little |
5201519 | Op-Id | Cullen Farms |
5201520 | Op-Id | Antonio and Janelle Vilchis |
5201521 | Op-Id | Kevin Randel |
5201522 | Op-Id | Tim Russo |
5201523 | RMP | Brian Madison |
5201524 | Op-Id | Todd Hughes |
5201525 | Op-Id | Beverly Ross |
5201526 | Op-Id | Wooters Bee Farms | Daren Wooters
5201527 | RMP | Warren Hicks |
5201528 | Op-Id | Pacific Gas and Electric | Kyle Keller
5201529 | Op-Id | Nick Simpson |
5201530 | Op-Id | Donald Marotz |
5201531 | Op-Id | Paynes Creek Sportsmans Club | Tami Leathers
5201532 | RMP | Nick McGowan |
5201533 | Op-Id | Dalia's and Sons Farms |
5201534 | Op-Id | Leonel Torres Bustos |
5201535 | Op-Id | Salomon Meza |
5201561 | Op-Id | Steven Parks |
5201564 | Op-Id | Carlos Hernandez |
5201572 | RMP | Curt Hubbard |
5201579 | RMP | Scott Sosebee |
5201592 | Op-Id | Linda G. Young | Linda G. Young
5201604 | Op-Id | Don Brown |
5201605 | RMP | Donavin Wenz |
5201609 | Op-Id | Gary Taylor |
5201633 | Op-Id | Jerry Jackson |
5201636 | RMP | Collins Pine Company |
5260220 | RMP | Nate Oliva |
5800102 | RMP | Nagra Farms | Sukhbir Nagra
5800325 | RMP | Nick Sohrakoff |
"""

def main():
    rows = []
    seen = set()
    for line in ROWS.strip().splitlines():
        parts = [html.unescape(p.strip()) for p in line.split(" | ")]
        if len(parts) < 3:
            raise SystemExit("bad line: " + line)
        while len(parts) < 4:
            parts.append("")
        pid, ptype, name, agent = parts[:4]
        if not pid.isdigit() or not name:
            raise SystemExit("bad row: " + line)
        if pid in seen:
            raise SystemExit("duplicate permit: " + pid)
        seen.add(pid)
        rows.append([pid, name.upper(), ptype, "Tehama", agent.upper()])
    with io.open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["operator_id", "name", "entity_type", "county", "agent"])
        w.writerows(rows)
    n_ag = sum(1 for r in rows if r[4])
    print("wrote " + OUT + ": " + str(len(rows)) + " permits (" + str(n_ag) + " with an agent of record)")

if __name__ == "__main__":
    main()
