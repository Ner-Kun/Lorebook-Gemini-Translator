import sys
import os
import re
import subprocess
import requests
import json
import logging
import random
import hashlib
import collections
import time
import copy
import base64

from PySide6 import QtWidgets, QtCore, QtGui 
import qdarktheme

from rich.logging import RichHandler
from rich.console import Console
from rich.theme import Theme
from rich.highlighter import ReprHighlighter


ICON_BASE64_DATA = """
iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAYAAADDPmHLAAAAIGNIUk0AAHomAACAhAAA+gAAAIDoAAB1MAAA6mAAADqYAAAXcJy6UTwAAAAGYktHRAD/AP8A/6C9p5MAAAAHdElNRQfpBhcPJTKUabw2AAAoEklEQVR42u2daZAd13WYv9P99jf7YABisAMDEgBJcQFJCRRESqQsi6YYUYkkL2XZjiS7slQSx4l/xIkdu5Kyy5VNrrKqopQTeYtsRbJMS5Rk2VooigRJiZRIigIJYuGAIAbb7Mvbu09+dPfr/c0AeM+GrTmowUx337597znnnr1vwzqswzqswzqswzqswzqswzqswzqswzqswzqswzqswzqswzqswzr8vQX5m3rQnsMPM3P6VcxMhnqjjhgZJJNFDANsUNQfjcbvV1VEvMuSMHB1piOAamhq2r4rPmUlDQnpV0ScR7TH0/5b3Lu0fT7UjyTPTVBsu4U26mTyRdS22bRtgleffKTndOk5A2y56TBzMxcRIFvsY3DHDVx48VvFbGlw0Mjm+kSMrKpKEFGKuoeioC4+XSwHECgiqv4JwWUMdSnS/jsw0zCPiUclRDzqCIrTbZDAiAhtJmxTUv2/JTAOnHG3WTHIjNpuIoHhqNVabCwtzG7cf7C6+MZJKrPnyZb6GJ84wPEnH+0ZfXrKAP1b9tJcWaIwupmVi1O58obNB81c4QEjkzkkhrENMfqAjEuJpOEEuSIB16H1lD4X7XBVV70Th5jesg8+KshdDpf492nkGYkPEbepgi5j25N2q/nVZnXlc+O33fPqmWe/jhgGG7dPcPLJz/eERj1hgIm7H2Lq5FEEZfPtP8Kll48czBb6fsnI5h4QMzPs485dqWIAitqKJsnIlIGvhfpR+mqkfRr9o+fFMACwldQRKslaTADD007uHKPtBNp4sFutk1az9tuL51//ZKF/uIUqS2df6QWpus8AE3c/yLlTxwBYOT9pjkzc8jOZQvk3JJPdhipiGGT7hikMjpHJl6gvTrMyfQaAoS17yJdHElAYGW4Ie5rcJkQW77zG+wg2i3GKw6D1pVkWpk6iCvsKsC3ri3IJ9q8a4kyvy4sWvFh1Wg5u3klhcENARgiojdWoUJm7QG1h1rlXrWqrVvm1mWPf/u/lTXvswsAQM8ef6za5yHS7wwuTr6JWi8qlSWNk4o5/kSn1/WfDNMuKUNy4h6G9hxjeeTO58hBmNs+lF7/Myrc+jRiw4+73MrL7EGpbsX7TyLratbWAdLhHDIPpV4+w+MjvoKp8YBB+aliw2sI/qL1cbRXozBT462X412fBArbe+W42HrgvMEeHcWxt0VyZ4eLRx3n9mS/RqlWLmXzx34/sue0FyeT+urIw021SAWB0s7M9hx9maeo4A+MTDO++9QOZYvk3DNMsSybPyM0PsOnuD9O//c3k+jdimHlETEe9tlWpuEMyA79NEBMl+GOEriuG+xO8Frg/dBw97/QZb+P3GUSTqZBRG1PV/0HDx4HzGfdaGOVmaAwqJmLkyQ1sYduhn2Di/p/EyGYRwxwy86V/vjw9VTAMg+vf9uC1zQBTr3yXwe03Upl+Y2+m2PfrRiY7IGaO0Vv/AUM3/AhiFlG1A8Qm8Lf3E4ROazlNc1896Bp7kkBb7dRZ4AbtpLJUURvGDtzPholbHdc3k3lrsX9oXzZX6MrcotA1Bthz6D2gNvOnXyJbHvh5I5vfp6oMXv82+nceAlXENX6k7RiJS/xVUH7FdO1krmlqm06GUdDsSDIo0x4v7eN479EzYhQY3XM7IoIYxoiRzR3IFMsgXdfYXZQAqmQKZfq37ttm5PLvBcgPb2Fw771X8JjEaEkHkMtpHLkuq7bo2E4jjNCBWUWSetHEw1z/GEYmiyCGYWa35op9COZl4nF16BoD3HTPA2RLA2TzpYOGmdkF0L/jIGZhEDyx72EhhrCo+I8cJ8ZaElGccny5zs7q6qjdQpKf2sktDTeW+M2AYWbaHKOQN/PXuAp4/DOfoLxxG0Yme5uIkTVzJYqbbnAc5xACoihYq8YNNovekybOdZXrac9POidr6il9Rl7EMW1OaXP2fZTuWDhh6BoDiGQ48+TnENPcDkqmNIxZHIoNWyIBMt8ATCMeiGs/xDpIx9pVXu/YNJENgxIhZRYdu4tKDQ08xcsp9CJq1zUGaDbqSHYwI2IMAZj5MoaZCzvFEZDIURICEVAJoCfUXS/WRMdBBgbqE0073BuT8LHQ4+pk9VTlscc/1/Xpdc2stBo1VC1RXEtFkjk+dCxJuJDYRcGVhN5RJ0MLl2FCGcF4EsEfTVJQuCNZQYMRwASeDfJq1PKXtIbJfTiX1xogv3zomgSwLQtardTrEnEAkyCs6XzRGMVbRwgtuY7sB2sw9KJXHXr67TwBZ+BE/aJpopQkkMvfl0FW6YUC6GooWAGbqMwPJe7S4j1BYoccbQ2vEgl2n5LF7+SMdzy3+nV36IpjlgAO4VvAt6sw3UIPlZFRwwn7hnMVEYWnnZ8VfXKv0rbdYwDxqRNcySHBGwybJUi/TmGbuK7okMcL1Q0Exfkqon2NM1W3H0NgyYZPzsIfzsGyhRwqKf92o+hNecRu16iki/q1Qq9UQJclgIufILaIuvBJYjayygP3JSXp2hU3CUwg0kmwdsODcIoDTEM43oCPXVK+uuzIPkF5oiq8fhb5xTH4sX4HwYm8eJlwzUuAoJBKj9KnJdMVMEIKPxpyDUbc2hJBJQGpq+n91WeSJL0CzCgW8MVF+N1p5WRTMNSmPDJGrjTAwtnXeL2l/Op5eKUO/2RUMEXd+6VtzK51VEFW7wV0VwW4RROdxHpMnAfjAImZlWAFYDSI4FVexU9fOaTbDALM2uh/m0b+eFZZUSeXOLrnRna/46fJ92/kje88wpnv/BWVep3fmxVO1pXbSqIe6a9sJTs4mjj8ECee+MLVTC4GXWSAZNytKvU0IuhjYXr/fMgUUnXjA4EHSFDhdHPNuOtX4I/nkAUbLFvJ5wtsveOdbL3rfZiFIbBhx+EP0bdpt5567NOyPHOer68Iz1RVLBFX+0XGtaahajic3kXongpQT8hdjb5KSIykhv0dhGrsulwe/cV1TUO8FfBCwMnN4+j5WQtEbQY2bmH3vR9kZM8hp2bAC3mrwYbr75Xyhu289vinuHjse6zYGqoWDA41YfQJzqoghjj1E12G7qoAxwCTsAcfnJS0/yUGisSLkwki2pH+nrUfrw10zcS0cICTYgVstFWnVVvGqq9gNauAIkaOTL6EWejHzBbBEAY2X8/IrgPMnHoJM5tl07472Xn4A+SHtqOWHSOZ2jaFkV3c8OC/pH/zo5w+8kUa1RWMTIZModz2iDVBtSUrINfY6UEsoGsMYKv3H1H649XOaUA8xAM8QXm/FqMncKcI4ULLsK2gOKVdgk1z5RKL546xeOZlXb54RmqLszTrK1jNBqAYRpZMPk+uPER5w7gObr1eBrfeyP4H/ylL509hZovaN75PDNOp34+7KG4U0rYxzD623fVB+sZ26rkXH5Py2FYGt96Iqu0m+oI+TXRWobmqqqL2NcwAjrhM01NxvRypnww39Vqrb+gn9RdcN05fGusHMTDEonLpVS689BiXTjxPZe4SVqslNoAIBoLRZr0G1coKOjvD7JkTMvXCt8j3DTK660auu+V+BrbeLJBxiO8NlICXEopEKarC0O63yNCuOxAxUY3gISo9SDCD3AuypkTY5UEX3cDkwoakE8HVGppmgPiemIwHcfx17kXkPeSHXuQAxDRoLJ3n7HOPcu7FJ6gtLWCLQU5gPGewOw87czCehT43KF5TON+C03XhRF0424KVpUWqLzzJhVeeY+O+g2x/88MUN+xxbIXI8hVNmLqtgBnO6qXEsjqYPGBcwwzgyLTLTC3EwqHqx1oT0eL/Dq8zV8V4kWMRRGzmTz2lJx/7tCycO40twkDG4M1FePcA3F6EjRnIC7E6GxtoKMxY8GIN/nIJnlg2mGs0OPvCk8yffoVdh9/HxpveCZJz30SK4gNS9ViA+J0T4f4ZRdMF7FVAFyOBCVU8oYxW8i1hU0FS+o0jJGpEhXJz2uCNZz/P5BN/LvVajYxhcG8ZfnYE7ixC0VPT6jBNK8FCzwDXmTBehvvKwvdq8Ptzqo8tiawszPLKV/6Aytw5tt/94xiZPl+qXY4H0tHKTUhc9SAa1N1QcNBXDbj3q+XgOl6Nv46Vll9xvBC7xutH/oTJp75My7IZNYVfGIUPDsGAAZbSrukPcWBC3YKtTmrZRHlzQbhxs8ini/A/p5U5y2LyqS9hNWrsvu+jYOTbTOClIqIqKYia9gumKbGT2BlVtAc2QBfLwtuRQAnRa633Ro9DmUOJX0uEFmee+SyTR75Ey7LZlYPfHocPj0CfBAkfgFCgPvwjHiXVeRGkqPCPh+HXNgt9BtgIF17+NvXFc37bpBmlDF+EDnPpVfQ/DN2TAIYBhgkiwZRgaCrBWH5K5sC1+319niol2wh3vU4DLnz/r5g88igtVXbnlN/aLNxRBMtOx6dXqSsRdaWueoiqpZbCVENpuS+0FIfGyBQGFFXp6KYHVEM0x7BmFPeAKbqsApTQC7OJef+OJk87Odj2BFKxqm0ximGwfP4op775Z7SaTUYzwq9cJ3pHEbFSOMgQh9XmLZhqwkxLaQEZETaYquNZkSHTGYPHPy3g/8wpvzsNNVspDQ6x5+0/SaY4In4FUhJJ3fMSZ/e107Q36aAuuoGRQUZsAIegaTIvggkNnokq/HAsAQRtLnP6ic9QXZzDNAx+fhTuLbnEjzxGBGyB79fh0UV4ZsVhgIoKNo5OLBnI9oxyT7/w0ADsykJT4X/PKR+fhpoNxYEhbnj3RxjcfhDb22MgOv9QIYQ/ryCfrNVm7E1JaNdfDo3r51AKNzXmlVLdQzgB5IeTfbtfDGH6lSNMn3oJ2zB4e1n58cGgevDvNwRmbPjkrPLZBWHaAu+NJUMEMUwstZlrKbMt4fk6fH5B+ZkR4UIL/mBWqNtKcWCI/T/2EYZ3343aPoO2PYFwAYQ7eA0d+gnQaGAoFbM9ga4xgLrhz47Jrog4T44VBdLDaUESTzcLWPUFpr77NSzLYtgQPjIqOmAgViQiZyCcagn/6YLyxLJDrGw2y8B1Oxjevp/SyGbMfB9Ws0pl5iwzJ19g8fzrTDbgNy84j7RVKQ0Mse/BjzK86xC2rTH2DP4VriwIz6QdGo8hKRG7IPDqtx7pFrna0D0GsKMpy+SpJyQKgngJ/O6AFXeZiWGy8PoLzE+dQkV455YWBwcMadUlIIwc4k9Zwq+eU56uginK0Oad7Lz7vQztvA0zN0A0tLzlzlkuvvQNTj/9JaqLs4BSGt7Avgc+zPCuQ6itMRkWzEqH2SEaIkyndifMTNzzXk48/hfdIhnQCxWQmNiPTjBJuEv7WkcLWXH9YQG7xfSrz2K1WvQVhA8+XGEwL6w8VcC+ZKJujL8KfGxaeabiVO5et/8uJu7/WXL946htY3txfdf1U4VMYZQtd72foR03c+mVJ7FbTTYeuIe+zfudlR98xS0Q1UM1tKFVLEdBkM/97Y8iU4yc7EEAwIW/karg5EBQB6dcNbSCw2jzZUizMsP82ePYGOzb0uS23RaZolIes6g9m6N5NI/RMvj6CnxpwWGsDbtv4vp3/QJmcQTb3aTBYT2LZnUWtZohGmSK/Wy5/d2AiqpofeENCVEoHJLEyOTJFIdJ3pOMtqMbZPbVA2U9o3+3awID+tvDUsIM0xymdh0GJLxB046zOS3EoDJzhtqis6XKW/a2GCwr2gJzwKb09hrNHS3mv1Pks9/NalVFSuU+dr3tg5il0dAuJGrXOfPMZzj34uNYzbpLg0RvRQJ2jPiD9meTyZfYcus7dPyOhwXJppIuwUb1zwe7D+JYu/96eHdLwgIxwLYXmCTeAjiL1GqE+kt2k92bDKjMnMVqNsllhFt2tkJ6RUzI39DktI2++HRGDFXG9t5K3+Z9PvHdGMLS1EtMHvkCVrPlVgNd+YqT5WVOPfEXMrD1AP3jb0LVSm5HUjVTcjv/oPvZoO4VhNg2brKbpCiQo1vD+j3ayr89ZFIRtBF8iWJTnTuPrcpgQdkxZktMWwAvnjdksS6YGZPRvXeCZCGw+kWE6vx5rGYTMUxGJ+6kMLjV38kkKaMlxOaBQKs6x6VjT9KqV1k+f4KBLW8KK8SI2Ots/Ptuo+PwXOPJIJG4jg5PJ9kriAs92nrS15cJS8W2aVSWQKFcsBkuRajv5upPnDOwbCj0lymNbkvOzARu3bD/HQxuO+zYBx0QHgtQitBcOsPc5PPUGzUqcxdcJkoQdW7MILHfCAadsLS49L+G6wGcyYZ977Sphe8L/B1wA5M8gaDVpWrTqldRoJiDfJZgyBEAW4XlqgGqZIv9ZAr9fsFnoM/QGVuxLcuv+Ik2lvi4wFkAYhYwcyVglmZlxXGLE0uadJXVH+hXXSytRV9cAXRxf4AwWjpGtII4Ce0YEo8iJaYTQoamYBq4JV2hQEJYZIuRWLAStenWPN/YsBTMLEYmC7hvS9sJWSjx7aIIyjo+qFevhnQ3HdzWU0nmbThO3jEzG5qu+j/BQIoYmNkCoNQaUG8FevAQbEAh5xy06ivYzWpsXMGNGPzjBNNcA1NLGr96wbDouEkWjCm2ZrJn5OD1RA8igV2UAIZjekcTIKtMUBIvdoqHuYpATLLFPkRgpSYsVQPXA4XpWzfYaojQqCxTX7yAGBJ/XChhYQENoOn/iPMj7m8nL5gQ87ab2C2nutjMFdpbv0anpNHnp+AjMFLpVSyouyVhl7PRb9LpgCEZtv0TG1MYHEUElmoGZ+dMDmyJ5CJEuXFbi3zWptGoMzf5fQa23hqPTQTU0LlnP8ulH3zVmYpqLB2tajOw5WbGbnp/LOljN1ewGisAmLm8UyPhmRKddGIkiRiPBXasHLkq6HIksIOl0k7e007LpuLFew8iIYQaREp5wzbMTIZa0+boWZMfubnZfpQt8HK1yGPZQczhFly0uXD0aTa/6X4y/eOA3X5VqzS6jWyxTKOywuK519CIjBfXhnC8T5vy2F73ODAaEZrVWaxGFREh3zeMYDhh62C8VzqTMhJYjFo1XYfuZgNJ8J3d41AuJGU2cWZIyB66jKS2Q7h8eYjm/CzPHM9Qvx9yJhyr5/n87DDfWBhg1s5Iad8StelllmfO8fozj7D7vo+A5JwebZv+zfu54Uc/zMWjR7CajZC5IiLYrRoL5yexLQszV6Bv/KaYHS8CtfmzWK0mYhgUh6/zmV6S5uUHizWxltxtF1goe972MCe7bAd0ObaYZlKE3wRIfeEjYjfF2SigZdQm17+Rgc27WJmf5oXJDF89XeRU3wB/NTegl5pZEXG8g/79ZSona9TOtTj7vcfIlYfYcuf7kIz7dg8mG/a/gw03HHaO1cs4G9jNZU4f+RPmp06BbTOw9UZKY/vbgaK20tImK+dfRW2bXLmP8oZtMZfTm1QsFB5TAYEjL6Leoy1iumYEOgixOrUIzzAt1ddWd8GtkZQkA0PMPBuuP4hpGswuGfyHx4b41PQoM62seK6hKGRKBiOHB8j0G1hWi1NP/DnHv/JxKpeOI2JhmKZja0gOyRSRXAkjk6UyO8mrX/kEZ579Bmrb5PtH2HTr+zDMom9rurUJrco0S+deBYHSyGYKQ+Nu5DPuCXjnBCF9O4so8yj0gAm6LAE6UhfWHGePZoUc8F7+aLeybUZ23U7fhnEWL57l0isNxve1yA5nQi9RqA3F8Txj9w0w/dgizXmbqRePMPPaDxjdeSNDOw5QHBnHzBWxmg3qCxeYm/w+0ydeoL68iIiQKw2y9e6foTR2Y3tle0MxRFg6+z1qC86ncUZ2HMDM92FbgVfYA6ELJ7CnsfhOmhbwklC9kAI9yAZCmpLXVU9GSmQk3pejVv20caY8xvgt97L01U/RWlQWnl9mw71DwRSCw0M2lHYW2fRjJrNPLVE906S+tMDUi09y7qUjGNkshmmito3VbDpv/YqBmAaFcYONd07Qv/E21HbeLA6OyqrPc+nlxxzxX+pjw/V3OXkNCVoKCVVOCRVPsWxge6oKzfRd2K4UuhgIsgn7POkmXcipSUKIrlICGVw1trLppvsY2bYXVZull2ssH684M4s+UCG/McemB4bZ+M5+yntyZPpNMAW71aJZq2E1GiBg9pmUdmYYu6+PjQ+OYO44SyX7h1jGOZxvCbhdG8LciW+wdO44CmyYuIXyxol2rWAooCVxhy7m5npSIpLa6Lz30ZVDF1WA98GFIMajhGuntlKERDBHGIwFRLrR8KoyiyPsfNv7Wfrcx2jWqswcWSIzYFIYz8ffp1MwcgZ9+8uU95ZoLbVozllYKxZ2w0ayglkyyQ5nyAyYGFnDqXSzoWm8hJWbo9j4CbL2DWAI1ZmjnHv+UWdPgL4Btt7xIBg5CBiJGpYBqczdDkIGA14E4iPGNawC3NdcVmfS6Bu1UQx4hpOXEUxCWXTRWDaD229n9+H3cfwbf0pr0ebS1+YZe+cwhc25RCZwoslCdihLdjgb69rNOENoCwADW96gkv89Stb7kcWtvHHkk9QXpxHDYPud76K86Yb2vgHBko6weE9OmoWS4KE8OeoYlF39vgfQg28GdQxZaGBmkn6rxk758jDMDr6SVzXYfPt7aKzMM/n0l2nM2Fz8yhwb7hmgtKuQHqOKaKvVczMmmIssLf0Rs9+EpbNvALDxhtvYfPt72ro/6THefDpJAX/O0ZC1hsLY3YIubxCxWtVCAqZDyZeIwddmmDSUBTlGQfLsOPxTKMrrz3yF5pzFha/MM3R7mcE3lTGK5lW9Yu0ZoNXJOrNPTlO/6BhlIzv2MnH/z2FkB9qiPzXYFUwpr8YJ/tycqohr2Qto7xCy2hIKuFASOhe3kpNWjbc6QiUVbdmpiFFk5+EPkSsP8doTj9CoVJh9aoXKZJ3BW0qUdhYxCkZb3fgdpEDbJFEaM00WX6qw/HINu+4wxIY9N7L3XR8l17/F3zImNrBIUUgK4dOdaFcO2p3iLFcG3QsFewMNJrk1maD+nDxlHGgQyvf7jeP594j7IB5jKRh5ttzxD3F26voM82dPUj3bpH5hifymCqXdBYrb8mSHTMyc4e68EaeIWopVsWhcbLJyskZlskFr2Sl8yeTzbL31Xrbf/UHMwqgTCJPwWMKUFt96DT0q5igmYVdBsXqQEeiBDeCTKBq5Crp+UT0Xuzf4Z5JDQWhtuec8ueDuzbPrzdy8aYILL32Nqe99g5XZC1TPNqlNWRiFFbKDJrkRk8ygiVkykIy70WXTprVk0ZyzaMxatJZstOVEJk3TZGjLbra/5SGGd78FJBMo/fLH0Rk8aSdpVyJI6+g6XRV00QsIuoHuyCPES450SegWX+TKqvMNWw7+/+0to2wbszDClrs+wNi+w8y8+hSXjj3L4oXXadYq1CoWtXOOa+oUC/miur3/jzhTy5XKDI7vYdONhxmduBMzP+S8IBL4PHSQIaXjoNfg0UeipgIYuob7LhO6nQ4OkybJe0vcFcElXlB3ylospCQIbizr6U4l1z/O+B3/iOtu+VEq06dZnDrG0vnXqMxeoFFZoNWoY7eaqCqG6W4VVxqkPHId/Zt3M7htP8WRHRiZEmrbqG23o5/Js0keW/B6msgPJYNd28ZRbd2jlgfdfj1cVyOa6CqCP2icBYTA5bNDeBNJdQs0xSxT3nwTfeM3gd3CatWw6ivYjSp2qwYoRsYp7jRyJWezSMm4Wx84r5Glqa/VXbvLGX6crYweFIb2wA30hpugCf3PoCUjpP1hvUDmJOb7Xx54KiHkVds23je8xSyRLZeh7Efc2gUh3i4haoVGkDaeqxlnsI/4DP4uvBuYEAmMIcSLcUe/BJKGBk8HX+3QEo8CRRnqGY7x1sFZhKKEqz4naVYdi9xS+vArrawe2ADdqwfw/w8WQKW18SechO81knytyeXkcfikiGbgwiCJ967tCdEzIaWEprTTlA57URLSZRvA8P9MFGbhaLhoOL/vdxSPmq9uMF0eaOw4ZHr5Y0xpn9ZnVFF0xkKn8USWSw9WP3TTrnR2Ck1YLokU9v+MZL78vohRN1pxcDnE8dqtIfaXNNJV+9SEc51bpsRIEtAKIIaB0YNQcPfeC0icRQf+T80BSFBKktSjH+5ZQ+Q5vauu3hO+V4ivdAkMePWRSxA3wYrqLkMXbQDbtZbjU4kjiMDKDwjNpCypu/WcjzsnyhfL4gVyDK5JF+4qgr/YueAWd8FnBXtqu6j+eCSJXeLyPAUnnVa0+vPS8Hy6CV38fLywlhcYU6xc55qk3BGS9anCMpQwCuSH3HSDJi+8JPkd/a3Ri0lzCao2DTeNRv+8smi3zyT+sFsN1LYCGUAJvLLePejiq2EmGBGbsiODJ6kC70SEIqHMXRSZ+JTW8GFwDDH/NFqgGlqUmqbTCEbnnP/XUNiQKL7Vy/HEU18irFx6DbvV/RrAKHT39fBoutIx9UOIDCaD/cSfe7yqlIsyQdQM9FeeJ8Kjrldyn0l2RwITEj2V5KNEyKkBNKwyIxAM06Ayc4KpF74ZEImdJOTVQe+ygdEVq+KsFjHAMPBe2gimBkR0lQ2UO6Pvctv4LKRrap9+PeF+Cf+56vNVsZorzL/2kr72xGdlZfpc4OVSZ2si61r+XoCzF44dn6/Sduus2gKN6Skqr03TXJkBy6I6O4W3As8880UuHf2O800dIrtoJHmTa7aL1hCklegfGvqVIKf91Ee7+0DhR9B06eR7um3tVp3q/AWWp8+J8/2i4MNdm+FalgBitDdgCFFNRbBqCyxPPs3y68/TXJ5Graar/lzuNgS14dLJH6D6g+7Pcs2T8H9pfCFfJaRzgSG05bsAmdIghQ3bWZk65m1b18ZVt6GLyaD25HxlLkJt+gSzL36B+uzr7a90ZEQoFTOUCzkyGXPtLs7lRHGuGLpH8jVNyVZml2o0Wxa5/jEG9hyidN0+7GaVlalXQ5NXs/vj6nIyCNppQRGqF48x/eyf0arMYiuMDhQ4fOt23nbbDr1++ygjQyVyWdMzpTvlWDolmSIFd/GBef5BShombNaHtiiL+nJRDtRIP/GT8fsDIWeBxUqTf/abX5Bjp6fJDWxicO87QEyq08dDz5PL/R7TGqGLu4S5H4xwXmKjVZ1l9oXP06zMYohw/8Ed+q9+6i0c3L9ZsjlTwj4b0N62IWT6riVi4l7vRKzg9nVBSGsT/Sp1Gm0T+XatxgYILCw3yWX9by6rbTkbS8RYnp4wQReNQAJrSGguTjt77hrCzz54K7/8c2+V4cGCqmW7X9uMTk9dW7etEEJmWZIICJ0P0T+8i3fQ2k7OTAQdunAaxvk8rYae6+8ckqK8NDDA0HPCzzIA245EGtP4x/kyRrfI1YYuuoE2qB3O+Nk2D9+3X3/lo2+jr5gVtew0Gdx5/ZK8BuNrzzUqE/pnlXNJY/D+aD87eNKtaQjf52UCOhePhO6RKLuHA1TeBpGKUN82cRX0SYYu7g9AO2YPDmfvGR/k33zordJXyoquEuVJfEkygLDQKU9ZEF5ZSaHopBUf7C+R6Kv0geC/9h1p5e9VG80VhPsK0FuD94T/8LKijhlTeO3ly6TK6tBdG8DM+INX5eF3HGD3tiH3hQZZ5X5Cum8tqzZ0PrbUoqsxvhYT95aFVAniB228AwmfT+w/nOmUSMeG0WnbsnZEU9zGl02X1aDrH43yZtNfynLvwZ3JyzICInB+psKfffUo80tVHwFR2Z9mwxG9toorF4wQr9WlTNJDHe+NOBMJbUWEWsPi4uxy9GXQeB5BvS8adRe6u0mUu6uxrcrYcJntmwcD8fgOYBh87mtH+Y+f+DpimqF5R3HpHSSR2FmUwQii1zYS8I1+v6cddwxTIby+fWLGnh0hnvcuf2hHkw5OYsY02veEw9OREV/LH4/O5kvUmVWQFgqlQo5CPru2mxV2jY/ojs3DslxtXuVIUlmD8NJfa1+BQfYAVGGl1sSyLd8+SdRB13goOF8ssNRaao3tv3tGMkql1qBWbwj9uVWRp7bNu+7eLft2jbFUqXviUIPFwx6yPHxEbMT4gkwuognuWp+YiJYkye2bNUFWCrUMvbkbEXqqKWzpBoJ++X/8pZx4YzasWSL99Sr42T0bwFa23vUAardOicD0fIUz5xd181jfmvY2MQR2bR0gJJc7rmRWaZsKaw0uXU5fV3i3sLhUp5hfCxls0GvYBthx80Emj76A2tZzqNYWVxqFbz53mrtu3kJ6Hj8Mzr46nQipkR6CIZsepwhWgStJ1Ygolu3PN+zE2AGRJ7ZtWWCbl9X/WqBrLLU0fZFmdYVWrfJdtayjGMJfPHZUJs8uBIqFu5TRSuCRv03iX9XzQ5LerzW0Gyv+52bUnm1WV1gtlnIl0DUGOH7kUWhUGNp14FKrXv2UgXLi7Dwf+79PUam2XB3ZpUybxA+7j5rVpFEPHgdtV7qxeN79EKc2sFpnrHq1J8PpqlJZXlpkfvIVGssLf2Q1G98Sw+CzXz/Kf/n9I7pcbSHmZZX7dMRTFLovAWJxRnym6CFjiNCqL1GZOupYrLZ1tlmvHW3WVnoyy64ywJ7bDyPZHLm+oYvNlaV/Z7eapy2F//XIs/JL//XLfP/YJceyNw3EEH/XuNiPRH7884aIW0qW1Cb6O/r3lf/En3n1ffqenfe/gN1g4djXqc2dARHsZuOvl954+XSrVuXkkc93n9+63eHQ9gMsnjvNjsMPMX/62IO5cv/HJZPdYds2m0dK3H/nHt5+5y7du21EBso5shkz+NkWr/YpKQwUd/dcvAXqT5x0RGqmsO1X+t5e+8vfjvAVb2NzDTTytp8JlHI71BL1tpz3PD0REdVgqiCQ6/Qn5qZ3kMWVpv7crz8iL09OUxzZQrZ/jJWzL4Ha2K3mmcbS7MNiZL5bW5qnemny2mcAgPzQOFaryZY3vZXFc5OHMqW+3zKyuXscc9YmnzUYLBfoK2bJ57yNmv14XHiAkShe4qA7G5edrmroK6Xx3v2XctJykmm5zPS4cXCOtq28fnGJetNqj0dEUMuaaVWWfnH74ff88Uuf/h3GbngTU88/3nVa9YQB9r71Qd44/jKNpXmGtk7QWFnYkCsN/LRZKHxIzMwBMYyCM9mEVZoUfOsUt+9NqdzVQ2LuIl4nAATe+VPUtpt2q/Vtq175zdkTz325NLZDBWGlB6sfeoy64R03YUsGbTUY2n4Ds5M/GMsV+w4aZvZuyWT2IMYQ4V196WTTr8YjvYZOz4+PPhhOjLvBseS3agW1J+1m/cl6ZfmbpeGNM0vnJzEyWa6buJGTT36hJ3PqOd4mDj/E2ZdfwG7WyQ0MkysN0D++m8nH/tQwMv0ZslkMw/SXhQjtfXaFtu8rYvj1BsGduD3Fr+7WLYbh63UR98vgvvHmSHz1azo8Ujm6vv2/uN+Al4AxoG194NYu2Z7nLoCBENgqLlDSrerU94c/iCqeuFdtNdBGxZp46Oet2WPfpb6ySHF0E9WLU2zaMcGJp7/YM/r8jQrPiUPv4cA9D3Lk/32CVqtJvbIIYrjf3wlm7rX9hri2s4kh7Pl/ezTxPtnertd3+gsyQGglRvS6Boy99qptfwbe10GejvZKw/zNxMSp2whkINWdi1fuGHrJNzBO7BbZfIFcaYBmdYXR7Xs59VRvVvw6rEMIrkXziYmDbw8dn3jusb/tIf29hd4Um6/D3xlYZ4AfclhngB9yuCZtgHVw4OChe0LHzz3V/UjgugT4IYd1Bvghh3UGWId1WId1WId1WId1WId1+GGD/w+kjeXX2mMouQAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAyNS0wNi0yM1QxNTozNzozMyswMDowMGNEjHcAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMjUtMDYtMjNUMTU6Mzc6MzMrMDA6MDASGTTLAAAAKHRFWHRkYXRlOnRpbWVzdGFtcAAyMDI1LTA2LTIzVDE1OjM3OjUwKzAwOjAwsosGDgAAAABJRU5ErkJggg==
"""
APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_VERSION = "0.1.0"
SETTINGS_FILE = os.path.join(APP_DIR, "translator_settings.json")
LOG_FILE = os.path.join(APP_DIR, "translator.log")
MAX_RECENT_FILES = 10
RPM_COOLDOWN_SECONDS = 61
LOREBOOK_TEMPLATE = {"entries": {}}


logger = logging.getLogger('Lorebook_Gemini_Translator')


default_settings = {
    "api_keys": [],
    "current_api_key_index": 0,
    "gemini_model": "gemini-2.5-flash-lite-preview-06-17",
    "log_to_file": False,
    "show_log_panel": False,
    "log_level": "INFO",
    "enable_model_thinking": True,
    "thinking_budget_value": -1,
    "use_content_as_context": True,
    "recent_files": [],
    "target_languages": [],
    "available_source_languages": ["English"],
    "selected_target_language": "",
    "selected_source_language": "English",
    "manual_rpm_control": False,
    "api_request_delay": 6.0,
    "rpm_limit": 15,
    "rpm_warning_threshold_percent": 60,
    "rpm_monitor_update_interval_ms": 1000,
    "available_gemini_models": []
}
current_settings = default_settings.copy()
fh = None

def run_updater():
    logger.info("Downloading and launching the external updater script...")
    
    UPDATER_URL = "https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/update.bat"
    updater_path = os.path.join(APP_DIR, "update.bat")

    try:
        update_response = requests.get(UPDATER_URL, timeout=10)
        update_response.raise_for_status()
        with open(updater_path, "wb") as f:
            f.write(update_response.content)

        subprocess.Popen(updater_path, shell=True)
        sys.exit(0)
        
    except Exception as e:
        logger.error(f"FATAL: Failed to download or run the updater script: {e}", exc_info=True)
        from PySide6 import QtWidgets
        _ = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Automatic Update Failed")
        msg_box.setText("Could not start the automatic updater due to an error.")
        msg_box.setInformativeText(f"Please update manually from the project's GitHub page.\n\nError: {e}")
        msg_box.exec()
        sys.exit(1)


def check_and_trigger_update():
    LOCAL_APP_VERSION = APP_VERSION
    VERSION_URL = "https://raw.githubusercontent.com/Ner-Kun/Lorebook-Gemini-Translator/test/version.txt"
    
    logger.info("--- Verifying application and launcher versions... ---")

    try:
        response = requests.get(VERSION_URL, timeout=5)
        response.raise_for_status()
        content = response.text
        
        remote_versions = {}
        for line in content.splitlines():
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                remote_versions[key.strip()] = value.strip()
        
        REMOTE_APP_VERSION = remote_versions.get("APP_VERSION", "0.0.0")
        REMOTE_LAUNCHER_VERSION = int(remote_versions.get("LAUNCHER_VERSION", "0"))
        
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not check for updates (network error): {e}. Skipping check.")
        return
    except Exception as e:
        logger.error(f"Failed to parse version file: {e}. Skipping check.")
        return

    try:
        launcher_path = os.path.join(APP_DIR, "run_translator.bat")
        if not os.path.exists(launcher_path):
            local_launcher_version = 0
        else:
            with open(launcher_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                match = re.search(r'set\s+"LAUNCHER_VERSION=(\d+)"', content, re.IGNORECASE)
                local_launcher_version = int(match.group(1)) if match else 0
    except Exception as e:
        logger.warning(f"Could not read local launcher version: {e}. Assuming it's outdated.")
        local_launcher_version = 0

    update_reason = ""
    if REMOTE_APP_VERSION > LOCAL_APP_VERSION:
        update_reason = f"New application version available ({REMOTE_APP_VERSION})."
    elif REMOTE_LAUNCHER_VERSION > local_launcher_version:
        update_reason = f"A required launcher update is available (v{REMOTE_LAUNCHER_VERSION})."

    if not os.path.exists(os.path.join(APP_DIR, "run_translator.bat")):
        update_reason = "Launcher file 'run_translator.bat' is missing."

    if update_reason:
        logger.warning(f"Update required: {update_reason}")
        from PySide6 import QtWidgets
        _ = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle("Update Required")
        msg_box.setText(update_reason)
        msg_box.setInformativeText("The application will now close and run the updater.")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        if msg_box.exec() == QtWidgets.QMessageBox.Ok:
            run_updater()
        else:
            logger.info("User cancelled the update. Exiting application to prevent issues.")
            sys.exit(0)
    else:
        logger.info("OK. Application and launcher are up to date.")

class JobSignals(QtCore.QObject):
    job_completed = QtCore.Signal(object, str, str)
    job_failed = QtCore.Signal(object, str, str, str, object, dict)
    inspector_update = QtCore.Signal(str, str, str, dict)

class TranslationJobRunnable(QtCore.QRunnable):
    def __init__(self, app_ref, job_data, signals):
        super().__init__()
        self.app_ref = app_ref
        self.job_data = job_data
        self.signals = signals

    @QtCore.Slot()
    def run(self):
        text_to_translate_for_log = self.job_data.get('text_to_translate', 'Unknown Text')
        model_name_requested_for_this_job = self.job_data.get('model_name')
        api_key_for_this_job = self.job_data.get('api_key')

        try:
            text_to_translate = self.job_data['text_to_translate']
            source_lang = self.job_data['source_lang']
            target_lang = self.job_data['target_lang']
            context_content_for_api = self.job_data['context_content_for_api']
            masked_key_log_text = self.app_ref._mask_api_key(api_key_for_this_job)
            
            logger.info(f"Job starting with API key: {masked_key_log_text}, Model: {model_name_requested_for_this_job}")
            
            client = genai.Client(api_key=api_key_for_this_job)
            prompt, final_processed_translation, thinking_text, usage_meta = self.app_ref._execute_gemini_api_call_internal(
                client, 
                model_name_requested_for_this_job, 
                text_to_translate, 
                source_lang, 
                target_lang, 
                context_content_for_api
            )
            self.signals.inspector_update.emit(
                prompt, 
                final_processed_translation if final_processed_translation is not None else "", 
                thinking_text,  
                usage_meta
            )

            if final_processed_translation is not None:
                self.signals.job_completed.emit(self.job_data, final_processed_translation, thinking_text)
            else:
                extra_details_for_general_failure = {'model_name_from_job': model_name_requested_for_this_job}
                self.signals.job_failed.emit(
                    self.job_data, 
                    "API call failed or returned no text.", 
                    thinking_text, 
                    "The API returned an empty or null response.",
                    None,
                    extra_details_for_general_failure
                )

        except (ResourceExhausted, errors.ClientError) as e_quota:
            error_message_str = str(e_quota)
            if "429" not in error_message_str and "RESOURCE_EXHAUSTED" not in error_message_str.upper():
                logger.warning(f"Caught {type(e_quota).__name__} but it is not a 429/ResourceExhausted error. Re-raising to generic handler.")
                raise e_quota

            masked_key_log_text_err = self.app_ref._mask_api_key(api_key_for_this_job)
            logger.error(f"Quota Error for '{text_to_translate_for_log}' (Key: {masked_key_log_text_err}): {e_quota}", exc_info=False)
            
            extra_details = {'model_name_from_job': model_name_requested_for_this_job}
            retry_delay_match = re.search(r"['\"]retryDelay['\"]\s*:\s*['\"](\d+)s['\"]|retry_delay\s*{\s*seconds:\s*(\d+)\s*}", error_message_str, re.IGNORECASE)
            if retry_delay_match:
                try:
                    delay_str = retry_delay_match.group(1) or retry_delay_match.group(2)
                    if delay_str:
                        extra_details['retry_delay_seconds'] = int(delay_str)
                        logger.info(f"Extracted retry_delay_seconds via regex: {extra_details['retry_delay_seconds']}.")
                except (ValueError, TypeError):
                    logger.warning("Failed to parse retry_delay seconds from regex match.")
            else:
                logger.warning("Could not find 'retryDelay' pattern in ResourceExhausted message.")

            quota_match = re.search(r"['\"]quotaValue['\"]\s*:\s*['\"](\d+)['\"]", error_message_str, re.IGNORECASE)
            if quota_match:
                try:
                    extra_details['quota_value_from_error'] = int(quota_match.group(1))
                    logger.info(f"Extracted quota_value via regex: {extra_details['quota_value_from_error']}.")
                except ValueError:
                    logger.warning("Failed to parse quota_value from error message regex match.")
            else:
                logger.warning("Could not find 'quotaValue: N' pattern in ResourceExhausted message.")
            
            self.signals.job_failed.emit(self.job_data, str(e_quota), "N/A - Quota Error", f"Quota Error: {e_quota}", e_quota, extra_details)

        except Exception as e:
            masked_key_log_text_err_gen = self.app_ref._mask_api_key(api_key_for_this_job)
            logger.error(f"Generic Exception in TranslationJobRunnable for '{text_to_translate_for_log}' (Key: {masked_key_log_text_err_gen}, Requested Model: {model_name_requested_for_this_job}): {e}", exc_info=True)
            extra_details = {'model_name_from_job': model_name_requested_for_this_job}
            self.signals.job_failed.emit(self.job_data, str(e), "N/A", f"Exception: {e}", e, extra_details)



def setup_logger():
    global fh
    logger.setLevel(getattr(logging, current_settings.get("log_level", "INFO").upper(), logging.INFO))
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if not current_settings.get("log_to_file", False) and fh is not None:
        logger.removeHandler(fh)
        fh.close()
        fh = None
    elif current_settings.get("log_to_file", False) and fh is None:
        try:
            fh = logging.FileHandler(LOG_FILE, encoding='utf-8', mode='a')
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"ERROR: Failed file logging: {e}")
            current_settings["log_to_file"] = False

def load_settings():
    global current_settings
    current_settings = default_settings.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                loaded_s = json.load(f)
                if "api_key" in loaded_s and isinstance(loaded_s["api_key"], str):
                    if "api_keys" not in loaded_s:
                        current_settings["api_keys"] = [loaded_s["api_key"]] if loaded_s["api_key"].strip() else []
                        current_settings["current_api_key_index"] = 0
                        logger.info("Migrated old 'api_key' to 'api_keys' list.")
                    del loaded_s["api_key"]
                for key in default_settings:
                    if key in loaded_s:
                        if key == "api_keys":
                            if isinstance(loaded_s[key], list):
                                current_settings[key] = [str(k) for k in loaded_s[key] if isinstance(k, str) and k.strip()]
                            else:
                                logger.warning(f"Setting '{key}' in file is not a list, using default.")
                        elif isinstance(default_settings[key], bool) and isinstance(loaded_s[key], bool):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], (int, float)) and isinstance(loaded_s[key], (int, float)):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], str) and isinstance(loaded_s[key], str):
                            current_settings[key] = loaded_s[key]
                        elif isinstance(default_settings[key], list) and isinstance(loaded_s[key], list):
                            if key not in ["api_keys"]:
                                current_settings[key] = loaded_s[key]
                if not isinstance(current_settings.get("api_keys"), list):
                    current_settings["api_keys"] = []
                num_keys = len(current_settings["api_keys"])
                if num_keys == 0:
                    current_settings["current_api_key_index"] = 0
                else:
                    loaded_idx = current_settings.get("current_api_key_index", 0)
                    if not (0 <= loaded_idx < num_keys):
                        logger.warning(f"Loaded current_api_key_index {loaded_idx} out of bounds ({num_keys} keys). Resetting to 0.")
                        current_settings["current_api_key_index"] = 0
                if "recent_files" in current_settings:
                    if not isinstance(current_settings["recent_files"], list):
                        current_settings["recent_files"] = []
                    current_settings["recent_files"] = [f for f in current_settings["recent_files"] if isinstance(f, str) and f][:MAX_RECENT_FILES]
                else:
                    current_settings["recent_files"] = []
                if "target_languages" not in current_settings or not isinstance(current_settings["target_languages"], list):
                    current_settings["target_languages"] = []
                current_settings["target_languages"] = [str(lang) for lang in current_settings["target_languages"] if lang]
                if "available_source_languages" not in current_settings or not isinstance(current_settings["available_source_languages"], list):
                    current_settings["available_source_languages"] = default_settings["available_source_languages"]
                current_settings["available_source_languages"] = [str(lang) for lang in current_settings["available_source_languages"] if lang]
                if not current_settings["available_source_languages"]:
                    current_settings["available_source_languages"] = ["English"]
                if "selected_target_language" not in current_settings:
                    current_settings["selected_target_language"] = ""
                if "selected_source_language" not in current_settings:
                    current_settings["selected_source_language"] = default_settings["available_source_languages"][0]
                if current_settings["selected_source_language"] not in current_settings["available_source_languages"]:
                    if current_settings["available_source_languages"]:
                        current_settings["selected_source_language"] = current_settings["available_source_languages"][0]
                    else:
                        current_settings["selected_source_language"] = "English"
        except Exception as e:
            print(f"ERROR: Failed settings load: {e}. Using defaults.")
            current_settings = default_settings.copy()
        finally:
            if not current_settings.get("available_source_languages"):
                current_settings["available_source_languages"] = ["English"]
            if not current_settings.get("selected_source_language") or current_settings["selected_source_language"] not in current_settings["available_source_languages"]:
                current_settings["selected_source_language"] = current_settings["available_source_languages"][0]
            if not current_settings.get("gemini_model"):
                current_settings["gemini_model"] = default_settings["gemini_model"]
            if not isinstance(current_settings.get("api_keys"), list):
                current_settings["api_keys"] = []
            if not isinstance(current_settings.get("current_api_key_index"), int) or current_settings.get("current_api_key_index") < 0:
                current_settings["current_api_key_index"] = 0
            if current_settings["api_keys"] and current_settings["current_api_key_index"] >= len(current_settings["api_keys"]):
                current_settings["current_api_key_index"] = 0
    else:
        pass
    if "available_gemini_models" not in current_settings or not isinstance(current_settings["available_gemini_models"], list):
        current_settings["available_gemini_models"] = []
    current_settings["available_gemini_models"] = [str(model) for model in current_settings["available_gemini_models"] if model]
    setup_logger()

def save_settings():
    try:
        if not current_settings["api_keys"]:
            current_settings["current_api_key_index"] = 0
        else:
            num_keys = len(current_settings["api_keys"])
            if not (0 <= current_settings["current_api_key_index"] < num_keys):
                current_settings["current_api_key_index"] = 0
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_settings, f, ensure_ascii=False, indent=2)
        logger.info("Settings saved.")
    except Exception as e:
        logger.error(f"Failed to save settings: {e}")

class QtLogHandler(logging.Handler):
    def __init__(self, text_widget):
        super().__init__()
        self.widget = text_widget
        self.widget.setReadOnly(True)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.setLevel(logging.DEBUG)
    def emit(self, record):
        if self.widget and self.widget.isVisible():
            msg = self.format(record)
            self.widget.append(msg)
            self.widget.moveCursor(QtGui.QTextCursor.End)

class ModelInspectorDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Inspector")
        self.setMinimumSize(700, 650)
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        
        layout = QtWidgets.QVBoxLayout(self)

        self.prompt_label = QtWidgets.QLabel("Last Prompt Sent to Model:")
        self.prompt_text_edit = QtWidgets.QTextEdit()
        self.prompt_text_edit.setReadOnly(True)
        layout.addWidget(self.prompt_label)
        layout.addWidget(self.prompt_text_edit, stretch=2)

        tokens_group = QtWidgets.QGroupBox("Usage Metadata")
        tokens_layout = QtWidgets.QHBoxLayout(tokens_group)
        self.prompt_tokens_label = QtWidgets.QLabel("Prompt: N/A")
        self.thinking_tokens_label = QtWidgets.QLabel("Thinking: N/A")
        self.response_tokens_label = QtWidgets.QLabel("Response: N/A")
        self.total_tokens_label = QtWidgets.QLabel("<b>Total: N/A</b>")
        tokens_layout.addWidget(self.prompt_tokens_label)
        tokens_layout.addStretch()
        tokens_layout.addWidget(self.thinking_tokens_label)
        tokens_layout.addStretch()
        tokens_layout.addWidget(self.response_tokens_label)
        tokens_layout.addStretch()
        tokens_layout.addWidget(self.total_tokens_label)
        layout.addWidget(tokens_group)

        self.thinking_groupbox = QtWidgets.QGroupBox("Model Thinking")
        self.thinking_groupbox.setVisible(False)
        
        thinking_layout = QtWidgets.QVBoxLayout(self.thinking_groupbox)
        self.thinking_text_edit = QtWidgets.QTextEdit()
        self.thinking_text_edit.setReadOnly(True)
        thinking_layout.addWidget(self.thinking_text_edit)
        
        layout.addWidget(self.thinking_groupbox, stretch=3)

        self.processed_translation_label = QtWidgets.QLabel("Final Translation:")
        self.processed_translation_text_edit = QtWidgets.QTextEdit()
        self.processed_translation_text_edit.setReadOnly(True)
        layout.addWidget(self.processed_translation_label)
        layout.addWidget(self.processed_translation_text_edit, stretch=1)
        
        self.setModal(False)

    @QtCore.Slot(str, str, str, dict)
    def update_data(self, prompt, final_translation_text, thinking_text, usage_metadata):
        self.prompt_text_edit.setPlainText(prompt)
        self.processed_translation_text_edit.setPlainText(final_translation_text)

        self.prompt_tokens_label.setText(f"Prompt: {usage_metadata.get('prompt', 'N/A')}")
        self.thinking_tokens_label.setText(f"Thinking: {usage_metadata.get('thoughts', 'N/A')}")
        self.response_tokens_label.setText(f"Response: {usage_metadata.get('candidates', 'N/A')}")
        self.total_tokens_label.setText(f"<b>Total: {usage_metadata.get('total', 'N/A')}</b>")
        self.thinking_tokens_label.setVisible('thoughts' in usage_metadata)

        if thinking_text and current_settings.get("enable_model_thinking", True):
            self.thinking_groupbox.setVisible(True)
            self.thinking_text_edit.setPlainText(thinking_text)
        else:
            self.thinking_groupbox.setVisible(False)
            self.thinking_text_edit.clear()

    def clear_data(self):
        self.prompt_text_edit.clear()
        self.processed_translation_text_edit.clear()
        self.thinking_text_edit.clear()
        self.thinking_groupbox.setVisible(False)
        self.prompt_tokens_label.setText("Prompt: N/A")
        self.thinking_tokens_label.setText("Thinking: N/A")
        self.response_tokens_label.setText("Response: N/A")
        self.total_tokens_label.setText("<b>Total: N/A</b>")

    def closeEvent(self, event):
        self.hide()
        event.ignore()

class ManageLanguagesDialog(QtWidgets.QDialog):
    def __init__(self, current_languages, language_type="Target", parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Manage {language_type} Languages")
        self.setMinimumWidth(350)
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.languages = list(current_languages)
        self.language_type = language_type
        layout = QtWidgets.QVBoxLayout(self)
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.addItems(self.languages)
        layout.addWidget(self.list_widget)
        input_layout = QtWidgets.QHBoxLayout()
        self.lang_input = QtWidgets.QLineEdit()
        self.lang_input.setPlaceholderText("Enter language name (e.g., Ukrainian)")
        input_layout.addWidget(self.lang_input)
        add_button = QtWidgets.QPushButton("Add")
        add_button.clicked.connect(self.add_language)
        input_layout.addWidget(add_button)
        layout.addLayout(input_layout)
        remove_button = QtWidgets.QPushButton("Remove Selected")
        remove_button.clicked.connect(self.remove_language)
        layout.addWidget(remove_button)
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def add_language(self):
        lang_name = self.lang_input.text().strip()
        if lang_name and lang_name not in self.languages:
            self.languages.append(lang_name)
            self.languages.sort()
            self.list_widget.clear()
            self.list_widget.addItems(self.languages)
            self.lang_input.clear()
        elif lang_name in self.languages: 
            QtWidgets.QMessageBox.information(self, "Duplicate", f"Language '{lang_name}' already exists.")
        elif not lang_name:
            QtWidgets.QMessageBox.warning(self, "Empty Name", "Language name cannot be empty.")

    def remove_language(self):
        selected_items = self.list_widget.selectedItems()
        if not selected_items: 
            return
        if self.language_type == "Source" and len(self.languages) - len(selected_items) < 1:
            QtWidgets.QMessageBox.warning(self, "Cannot Remove", "At least one source language must remain.")
            return
        for item in selected_items:
            lang_to_remove = item.text()
            if lang_to_remove in self.languages:
                self.languages.remove(lang_to_remove)
        self.list_widget.clear()
        self.list_widget.addItems(self.languages)
    def get_languages(self): return self.languages

class AboutDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"About Lorebook Gemini Translator v{APP_VERSION}")
        self.setMinimumWidth(350)
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        layout = QtWidgets.QVBoxLayout(self)
        title_label = QtWidgets.QLabel("Lorebook Gemini Translator")
        title_font = title_label.font()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        version_label = QtWidgets.QLabel(f"Version: {APP_VERSION}")
        version_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        layout.addSpacing(20)
        author_label = QtWidgets.QLabel("Developed by: Ner_Kun")
        author_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author_label)
        github_link_label = QtWidgets.QLabel("<a href=\"https://github.com/Ner-Kun\">Ner_Kun on GitHub</a>")
        github_link_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        github_link_label.setOpenExternalLinks(True)
        layout.addWidget(github_link_label)
        layout.addStretch()
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)


class ExportSettingsDialog(QtWidgets.QDialog):
    def __init__(self, default_lore_name, available_target_langs, current_selected_target_lang, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Export LORE-book Settings")
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.setMinimumSize(450, 300)
        main_layout = QtWidgets.QVBoxLayout(self)
        name_group_box = QtWidgets.QGroupBox("LORE-book Name")
        name_layout = QtWidgets.QHBoxLayout(name_group_box)
        self.loreNameEdit = QtWidgets.QLineEdit(default_lore_name)
        name_layout.addWidget(self.loreNameEdit)
        main_layout.addWidget(name_group_box)
        lang_group_box = QtWidgets.QGroupBox("Select Languages to Include in Export")
        lang_scroll_area = QtWidgets.QScrollArea()
        lang_scroll_area.setWidgetResizable(True)
        lang_widget_container = QtWidgets.QWidget()
        self.lang_checkbox_layout = QtWidgets.QVBoxLayout(lang_widget_container)
        lang_scroll_area.setWidget(lang_widget_container)
        self.lang_checkboxes = {}
        if not available_target_langs:
            no_langs_label = QtWidgets.QLabel("No target languages configured. Please add languages in settings.")
            no_langs_label.setStyleSheet("color: orange;")
            self.lang_checkbox_layout.addWidget(no_langs_label)
        else:
            select_buttons_layout = QtWidgets.QHBoxLayout()
            select_all_button = QtWidgets.QPushButton("Select All")
            select_all_button.clicked.connect(self.select_all_langs)
            deselect_all_button = QtWidgets.QPushButton("Deselect All")
            deselect_all_button.clicked.connect(self.deselect_all_langs)
            select_buttons_layout.addWidget(select_all_button)
            select_buttons_layout.addWidget(deselect_all_button)
            select_buttons_layout.addStretch()
            self.lang_checkbox_layout.addLayout(select_buttons_layout)
            for lang_name in sorted(available_target_langs):
                checkbox = QtWidgets.QCheckBox(lang_name)
                if lang_name == current_selected_target_lang: 
                    checkbox.setChecked(True)
                self.lang_checkboxes[lang_name] = checkbox
                self.lang_checkbox_layout.addWidget(checkbox)
            self.lang_checkbox_layout.addStretch()

        lang_group_box_layout = QtWidgets.QVBoxLayout(lang_group_box)
        lang_group_box_layout.addWidget(lang_scroll_area)
        main_layout.addWidget(lang_group_box, stretch=1)
        options_layout = QtWidgets.QHBoxLayout()
        options_layout.addStretch()
        self.includeOriginalsCheck = QtWidgets.QCheckBox("Include original keys")
        self.includeOriginalsCheck.setChecked(False)
        self.includeOriginalsCheck.setToolTip("If checked, original LORE keys will be included alongside selected translations.\n If unchecked (default), only selected translated keys will be included.\n (If no translation exists for an original key for any selected language, the original key will be kept.)")
        self.includeOriginalsCheck.setEnabled(bool(available_target_langs))
        options_layout.addWidget(self.includeOriginalsCheck)
        main_layout.addLayout(options_layout)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)

    def select_all_langs(self):
        for checkbox in self.lang_checkboxes.values():
            checkbox.setChecked(True)

    def deselect_all_langs(self):
        for checkbox in self.lang_checkboxes.values():
            checkbox.setChecked(False)

    def accept_settings(self):
        if self.lang_checkboxes:
            selected_langs = [lang for lang, cb in self.lang_checkboxes.items() if cb.isChecked()]
            if not selected_langs:
                QtWidgets.QMessageBox.warning(self, "No Languages Selected", "Please select at least one language to include in the export, or cancel.")
                return
        self.accept()

    def get_export_settings(self):
        lore_name = self.loreNameEdit.text().strip()
        selected_target_languages = []
        if self.lang_checkboxes:
            selected_target_languages = [lang for lang, cb in self.lang_checkboxes.items() if cb.isChecked()]
        include_originals = self.includeOriginalsCheck.isChecked()
        return lore_name, selected_target_languages, include_originals


class SettingsDialog(QtWidgets.QDialog):
    clear_cache_requested = QtCore.Signal()
    def __init__(self, settings_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(550)
        flags = self.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.setWindowFlags(flags)
        self.settings_data = settings_data.copy()
        self.actual_api_keys_in_dialog = list(self.settings_data.get("api_keys", []))
        main_layout = QtWidgets.QVBoxLayout(self)
        tab_widget = QtWidgets.QTabWidget(self)
        api_tab = QtWidgets.QWidget()
        api_layout = QtWidgets.QFormLayout(api_tab)
        
        api_keys_group = QtWidgets.QGroupBox("API Keys")
        api_keys_layout = QtWidgets.QVBoxLayout(api_keys_group)
        self.apiKeysListWidget = QtWidgets.QListWidget()
        self.apiKeysListWidget.setToolTip("List of API keys. One key will be used per request, in rotation.")
        self._populate_api_keys_list()
        api_keys_layout.addWidget(self.apiKeysListWidget)
        
        api_keys_buttons_layout = QtWidgets.QHBoxLayout()
        self.addApiKeyButton = QtWidgets.QPushButton("Add Key")
        self.addApiKeyButton.clicked.connect(self.add_api_key)
        
        self.fetchModelsButton = QtWidgets.QPushButton("Fetch Models")
        self.fetchModelsButton.setToolTip("Connect to the API to get a list of available models.")
        self.fetchModelsButton.clicked.connect(self.fetch_models_from_api)
        
        self.removeApiKeyButton = QtWidgets.QPushButton("Remove Selected Key")
        self.removeApiKeyButton.clicked.connect(self.remove_api_key)
        
        api_keys_buttons_layout.addWidget(self.addApiKeyButton)
        api_keys_buttons_layout.addWidget(self.fetchModelsButton)
        api_keys_buttons_layout.addWidget(self.removeApiKeyButton)
        api_keys_layout.addLayout(api_keys_buttons_layout)
        api_layout.addRow(api_keys_group)

        self.modelCombo = QtWidgets.QComboBox()
        self._populate_models_combo()
        api_layout.addRow("Gemini Model:", self.modelCombo)

        api_layout.addRow(QtWidgets.QLabel("<b>API Limiting</b>"))
        self.rpmLimitSpin = QtWidgets.QSpinBox()
        self.rpmLimitSpin.setRange(1, 1000)
        self.rpmLimitSpin.setValue(self.settings_data.get("rpm_limit", default_settings["rpm_limit"]))
        self.rpmLimitSpin.setToolTip("Default Requests-Per-Minute (RPM) limit per key.\nThe app automatically calculates dispatch delay based on this, unless manual control is enabled.")
        api_layout.addRow("Default RPM Limit:", self.rpmLimitSpin)
        
        self.manualControlCheck = QtWidgets.QCheckBox("Enable Manual Dispatch Delay")
        self.manualControlCheck.setChecked(self.settings_data.get("manual_rpm_control", default_settings["manual_rpm_control"]))
        self.manualControlCheck.setToolTip("Check this to override the automatic delay calculation and set the value manually.\nBe careful with low values, as they can lead to API errors.")
        api_layout.addRow(self.manualControlCheck)

        self.delaySpin = QtWidgets.QDoubleSpinBox()
        self.delaySpin.setRange(0.1, 60.0)
        self.delaySpin.setSingleStep(0.1)
        self.delaySpin.setValue(self.settings_data.get("api_request_delay", default_settings["api_request_delay"]))
        self.delaySpin.setSuffix(" seconds")
        self.delaySpin.setToolTip("The delay between dispatching each translation job when manual control is enabled.")
        api_layout.addRow("Manual Dispatch Delay:", self.delaySpin)

        self.delayWarningLabel = QtWidgets.QLabel("")
        self.delayWarningLabel.setStyleSheet("color: orange;")
        self.delayWarningLabel.setWordWrap(True)
        api_layout.addRow(self.delayWarningLabel)
        
        self.rpmWarningSpin = QtWidgets.QSpinBox()
        self.rpmWarningSpin.setRange(10, 95)
        self.rpmWarningSpin.setSuffix(" %")
        self.rpmWarningSpin.setValue(self.settings_data.get("rpm_warning_threshold_percent", default_settings["rpm_warning_threshold_percent"]))
        self.rpmWarningSpin.setToolTip("The RPM usage percentage at which the status indicator turns orange.")
        api_layout.addRow("Warning Threshold:", self.rpmWarningSpin)

        self.manualControlCheck.toggled.connect(self.update_delay_control_state)
        self.delaySpin.valueChanged.connect(self.check_manual_delay_warning)
        self.rpmLimitSpin.valueChanged.connect(lambda: self.update_delay_control_state())
        self.update_delay_control_state(self.manualControlCheck.isChecked())
        
        self._update_fetch_button_state()

        self.clearCacheButton = QtWidgets.QPushButton("Clear Active LORE-book Cache")
        self.clearCacheButton.clicked.connect(self.on_clear_cache_clicked)
        api_layout.addRow(self.clearCacheButton)
        tab_widget.addTab(api_tab, "API & Model")
        
        log_tab = QtWidgets.QWidget()
        log_layout_main = QtWidgets.QVBoxLayout(log_tab)
        self.logToFileCheck = QtWidgets.QCheckBox("Log to file")
        self.logToFileCheck.setChecked(self.settings_data.get("log_to_file", default_settings["log_to_file"]))
        log_layout_main.addWidget(self.logToFileCheck)
        self.showLogPanelCheck = QtWidgets.QCheckBox("Show log panel")
        self.showLogPanelCheck.setChecked(self.settings_data.get("show_log_panel", default_settings["show_log_panel"]))
        log_layout_main.addWidget(self.showLogPanelCheck)
        log_level_layout = QtWidgets.QHBoxLayout()
        log_level_layout.addWidget(QtWidgets.QLabel("Log Level:"))
        self.logLevelCombo = QtWidgets.QComboBox()
        self.logLevelCombo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.logLevelCombo.setCurrentText(self.settings_data.get("log_level", default_settings["log_level"]).upper())
        log_level_layout.addWidget(self.logLevelCombo)
        log_layout_main.addLayout(log_level_layout)
        log_layout_main.addStretch()
        tab_widget.addTab(log_tab, "Logging")
        
        main_layout.addWidget(tab_widget)
        self.buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept_settings)
        self.buttonBox.rejected.connect(self.reject)
        main_layout.addWidget(self.buttonBox)

    def update_delay_control_state(self, is_manual=None):
            if is_manual is None: 
                is_manual = self.manualControlCheck.isChecked()
            self.delaySpin.setEnabled(is_manual)
            if not is_manual:
                rpm_limit = self.rpmLimitSpin.value()
                calculated_delay = 60.0 / rpm_limit if rpm_limit > 0 else 60.0
                self.delaySpin.blockSignals(True)
                self.delaySpin.setValue(calculated_delay)
                self.delaySpin.blockSignals(False)
            self.check_manual_delay_warning()

    def check_manual_delay_warning(self):
        if not self.manualControlCheck.isChecked():
            self.delayWarningLabel.hide()
            return
        manual_delay = self.delaySpin.value()
        rpm_limit = self.rpmLimitSpin.value()
        safe_delay = 60.0 / rpm_limit if rpm_limit > 0 else 60.0
        if manual_delay < safe_delay:
            self.delayWarningLabel.setText(f"Warning: Delay is faster than the calculated safe value (~{safe_delay:.2f}s) for {rpm_limit} RPM. This may cause API errors (429).")
            self.delayWarningLabel.show()
        else:
            self.delayWarningLabel.hide()

    def _mask_api_key_for_dialog(self, api_key_string):
        if len(api_key_string) > 7:
            return f"{api_key_string[:3]}...{api_key_string[-4:]}"
        elif len(api_key_string) > 0:
            return "****"
        return ""

    def _populate_api_keys_list(self):
        self.apiKeysListWidget.clear()
        for key_val in self.actual_api_keys_in_dialog:
            self.apiKeysListWidget.addItem(self._mask_api_key_for_dialog(key_val))

    def _update_fetch_button_state(self):
        has_keys = len(self.actual_api_keys_in_dialog) > 0
        self.fetchModelsButton.setEnabled(has_keys)

    def add_api_key(self):
        new_key, ok = QtWidgets.QInputDialog.getText(self, "Add API Key", "Enter API Key:", QtWidgets.QLineEdit.Password)
        if ok and new_key.strip():
            key_to_add = new_key.strip()
            if key_to_add not in self.actual_api_keys_in_dialog:
                self.actual_api_keys_in_dialog.append(key_to_add)
                self.apiKeysListWidget.addItem(self._mask_api_key_for_dialog(key_to_add))
                logger.info("API key added to dialog list (masked).")
                self._update_fetch_button_state()
            else: 
                QtWidgets.QMessageBox.information(self, "Duplicate Key", "This API key is already in the list.")
        elif ok and not new_key.strip():
            QtWidgets.QMessageBox.warning(self, "Empty Key", "API key cannot be empty.")

    def remove_api_key(self):
        current_row = self.apiKeysListWidget.currentRow()
        if current_row >= 0 and current_row < len(self.actual_api_keys_in_dialog):
            reply = QtWidgets.QMessageBox.question(self, "Remove API Key", "Are you sure you want to remove the selected API key?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.Yes:
                del self.actual_api_keys_in_dialog[current_row]
                self.apiKeysListWidget.takeItem(current_row)
                logger.info("API key removed from dialog list.")
                self._update_fetch_button_state()
        else: 
            QtWidgets.QMessageBox.warning(self, "No Selection", "Please select an API key to remove.")
    
    def fetch_models_from_api(self):
        fetched_models = []
        keys_to_try_fetch = self.actual_api_keys_in_dialog
        if not keys_to_try_fetch:
            logger.warning("Fetch Models button clicked, but no API keys are available.")
            QtWidgets.QMessageBox.warning(self, "No API Keys", "Please add at least one API key before fetching models.")
            return

        logger.info("Fetching models from API by user request...")
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            for key_val in keys_to_try_fetch:
                try:
                    masked_key_log = self._mask_api_key_for_dialog(key_val)
                    logger.info(f"Trying API key (masked: {masked_key_log}) for models in dialog...")
                    client = genai.Client(api_key=key_val)
                    models_from_api = [ m.name.replace("models/", "") for m in client.models.list() if m.name.startswith("models/gemini") ]
                    if models_from_api:
                        fetched_models = sorted(list(set(models_from_api)))
                        logger.info(f"Fetched models with key ({masked_key_log}): {fetched_models}")
                        break
                    else:
                        logger.warning(f"No models found for key ({masked_key_log}).")
                except Exception as e_key_fetch:
                    masked_key_log_err = self._mask_api_key_for_dialog(key_val)
                    logger.warning(f"Failed model fetch with key ({masked_key_log_err}): {e_key_fetch}", exc_info=False)
            
            if not fetched_models:
                logger.error("Failed to fetch models with any provided API keys for dialog.")
                QtWidgets.QMessageBox.warning(self, "Model Fetch Error", "Could not fetch models from the API with any of the provided keys. Please check your keys and internet connection.")
            else:
                self.settings_data["available_gemini_models"] = fetched_models
                self._populate_models_combo()
                QtWidgets.QMessageBox.information(self, "Success", f"Successfully fetched {len(fetched_models)} models from the API.")

        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def _populate_models_combo(self):
        current_selected_model = self.settings_data.get("gemini_model", default_settings["gemini_model"])
        final_model_list = self.settings_data.get("available_gemini_models", [])
        if current_selected_model and current_selected_model not in final_model_list:
            final_model_list.append(current_selected_model)
        final_model_list = sorted(list(set(final_model_list)))
        
        self.modelCombo.clear()
        if final_model_list:
            self.modelCombo.addItems(final_model_list)
            if current_selected_model in final_model_list:
                self.modelCombo.setCurrentText(current_selected_model)
            elif final_model_list:
                self.modelCombo.setCurrentIndex(0)
        else:
            self.modelCombo.setPlaceholderText("No models fetched yet")
            if current_selected_model:
                self.modelCombo.addItem(current_selected_model)
                self.modelCombo.setCurrentText(current_selected_model)

    def on_clear_cache_clicked(self): self.clear_cache_requested.emit()
    logger.info("Cache clear requested from settings.")

    def accept_settings(self):
        self.settings_data["api_keys"] = list(self.actual_api_keys_in_dialog)
        if not self.settings_data["api_keys"]: 
            self.settings_data["current_api_key_index"] = 0
        else:
            num_keys = len(self.settings_data["api_keys"])
            if self.settings_data.get("current_api_key_index", 0) >= num_keys: 
                self.settings_data["current_api_key_index"] = 0
        self.settings_data["gemini_model"] = self.modelCombo.currentText()
        self.settings_data["rpm_limit"] = self.rpmLimitSpin.value()
        self.settings_data["manual_rpm_control"] = self.manualControlCheck.isChecked()
        self.settings_data["api_request_delay"] = self.delaySpin.value()
        self.settings_data["rpm_warning_threshold_percent"] = self.rpmWarningSpin.value()
        self.settings_data["log_to_file"] = self.logToFileCheck.isChecked()
        self.settings_data["show_log_panel"] = self.showLogPanelCheck.isChecked()
        self.settings_data["log_level"] = self.logLevelCombo.currentText()
        self.accept()

    def get_settings(self): return self.settings_data

class FocusOutTextEdit(QtWidgets.QTextEdit):
    focus_out = QtCore.Signal()

    def focusOutEvent(self, event: QtGui.QFocusEvent):
        self.focus_out.emit()
        super().focusOutEvent(event)

class EditorTab(QtWidgets.QWidget):
    search_term_changed = QtCore.Signal(str)

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.selected_editor_entry_id = None
        self.editor_active_entry_copy = None
        self.is_saving_from_editor = False
        self.editor_widgets = {}

        self.editor_logic_map = {0: "AND ANY", 1: "NOT ALL", 2: "NOT ANY", 3: "AND ALL"}
        self.editor_strategy_map = {0: "🟢 Normal", 1: "🔵 Constant", 2: "🔗 Vectorized"}
        self.editor_position_map = {
            0: "↑ Before Character", 1: "↓ After Character", 2: "↑ Before Extension Memory",
            3: "↓ After Extension Memory", 4: "↑ Before Author's Note", 5: "↓ After Author's Note",
            6: "@ System Directive ⚙️", 7: "@ Persona Directive 👤", 8: "@ Character Directive 🤖"
        }
        self.editor_tri_state_map = {0: "Use Global", 1: "Yes", 2: "No"}
        
        self.editor_debounce_timer = self._create_debounce_timer(self.editor_save_entry_changes)
        
        self.init_ui()

    def init_ui(self):
        editor_layout = QtWidgets.QHBoxLayout(self)

        editor_left_panel = QtWidgets.QWidget()
        editor_left_layout = QtWidgets.QVBoxLayout(editor_left_panel)
        editor_left_panel.setMinimumWidth(350)
        editor_left_panel.setMaximumWidth(550)

        editor_left_layout.addWidget(QtWidgets.QLabel("LORE Entries"))
        
        self.editor_search_input = QtWidgets.QLineEdit()
        self.editor_search_input.setPlaceholderText("Search UID, Name, Comment...")
        self.editor_search_input.textChanged.connect(self.on_global_search_changed)
        editor_left_layout.addWidget(self.editor_search_input)
        
        self.editor_entry_table = QtWidgets.QTableWidget()
        self.editor_entry_table.setColumnCount(3)
        self.editor_entry_table.setHorizontalHeaderLabels(['UID', 'Primary Keywords', 'Comment'])
        self.editor_entry_table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.editor_entry_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.editor_entry_table.itemSelectionChanged.connect(self.editor_load_entry_details)
        self.editor_entry_table.setWordWrap(False)
        header = self.editor_entry_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeMode.Stretch)
        editor_left_layout.addWidget(self.editor_entry_table)

        editor_button_layout = QtWidgets.QHBoxLayout()
        self.editor_add_btn = QtWidgets.QPushButton("+ Add")
        self.editor_add_btn.clicked.connect(self.editor_add_entry)
        self.editor_duplicate_btn = QtWidgets.QPushButton("⧉ Duplicate")
        self.editor_duplicate_btn.clicked.connect(self.editor_duplicate_entry)
        self.editor_delete_btn = QtWidgets.QPushButton("− Delete")
        self.editor_delete_btn.clicked.connect(self.editor_delete_entry)
        editor_button_layout.addWidget(self.editor_add_btn)
        editor_button_layout.addWidget(self.editor_duplicate_btn)
        editor_button_layout.addWidget(self.editor_delete_btn)
        editor_left_layout.addLayout(editor_button_layout)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)

        self.editor_form_widget = QtWidgets.QWidget()
        scroll_area.setWidget(self.editor_form_widget)
        editor_right_layout = QtWidgets.QVBoxLayout(self.editor_form_widget)
        self.editor_form_widget.setEnabled(False)
        basic_info_group = QtWidgets.QGroupBox("Basic Information")
        basic_info_layout = QtWidgets.QFormLayout(basic_info_group)
        self.editor_widgets['enabled_check'] = QtWidgets.QCheckBox("Entry Enabled")
        self.editor_widgets['comment_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['keys_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['keysecondary_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['content_edit'] = FocusOutTextEdit()
        self.editor_widgets['content_edit'].setAcceptRichText(False)
        self.editor_save_status_label = QtWidgets.QLabel("Select an entry to edit.")
        self.editor_save_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        first_row_layout = QtWidgets.QHBoxLayout()
        first_row_layout.setContentsMargins(0,0,0,0)
        first_row_layout.addWidget(self.editor_widgets['enabled_check'])
        first_row_layout.addStretch()
        first_row_layout.addWidget(self.editor_save_status_label)
        basic_info_layout.addRow(first_row_layout)
        basic_info_layout.addRow("Title/Memo (Comment):", self.editor_widgets['comment_edit'])
        basic_info_layout.addRow("Primary Keywords:", self.editor_widgets['keys_edit'])
        basic_info_layout.addRow("Secondary Keywords:", self.editor_widgets['keysecondary_edit'])
        editor_right_layout.addWidget(basic_info_group)
        editor_right_layout.addWidget(QtWidgets.QLabel("Content:"))
        editor_right_layout.addWidget(self.editor_widgets['content_edit'], stretch=1)
        activation_group = QtWidgets.QGroupBox("Activation & Placement")
        activation_layout = QtWidgets.QHBoxLayout(activation_group)
        self.editor_widgets['logic_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['logic_combo'].addItems(self.editor_logic_map.values())
        self.editor_widgets['position_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['position_combo'].addItems(self.editor_position_map.values())
        self.editor_widgets['strategy_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['strategy_combo'].addItems(self.editor_strategy_map.values())
        self.editor_widgets['order_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['probability_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['useProbability_check'] = QtWidgets.QCheckBox("Use Probability")
        self.editor_widgets['depth_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['depth_edit'].setPlaceholderText("Depth")
        self.editor_widgets['depth_edit'].setValidator(QtGui.QIntValidator(0, 999))
        self.editor_widgets['depth_edit'].setFixedWidth(60)
        activation_layout.addWidget(QtWidgets.QLabel("Logic:"))
        activation_layout.addWidget(self.editor_widgets['logic_combo'])
        activation_layout.addWidget(QtWidgets.QLabel("Strategy:"))
        activation_layout.addWidget(self.editor_widgets['strategy_combo'])
        position_layout = QtWidgets.QHBoxLayout()
        position_layout.setContentsMargins(0,0,0,0)
        position_layout.addWidget(QtWidgets.QLabel("Position:"))
        position_layout.addWidget(self.editor_widgets['position_combo'])
        position_layout.addWidget(self.editor_widgets['depth_edit'])
        activation_layout.addLayout(position_layout)
        activation_layout.addWidget(QtWidgets.QLabel("Order:"))
        activation_layout.addWidget(self.editor_widgets['order_edit'])
        activation_layout.addWidget(QtWidgets.QLabel("Trigger %:"))
        activation_layout.addWidget(self.editor_widgets['probability_edit'])
        activation_layout.addWidget(self.editor_widgets['useProbability_check'])
        self.editor_widgets['position_combo'].currentIndexChanged.connect(self._update_insertion_depth_visibility)
        editor_right_layout.addWidget(activation_group)
        scan_group = QtWidgets.QGroupBox("Scanning Options")
        scan_layout = QtWidgets.QHBoxLayout(scan_group)
        self.editor_widgets['scanDepth_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['scanDepth_edit'].setPlaceholderText("Global")
        self.editor_widgets['scanDepth_edit'].setValidator(QtGui.QIntValidator(0, 9999))
        self.editor_widgets['caseSensitive_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['caseSensitive_combo'].addItems(self.editor_tri_state_map.values())
        self.editor_widgets['matchWholeWords_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['matchWholeWords_combo'].addItems(self.editor_tri_state_map.values())
        self.editor_widgets['useGroupScoring_combo'] = QtWidgets.QComboBox()
        self.editor_widgets['useGroupScoring_combo'].addItems(self.editor_tri_state_map.values())
        scan_layout.addWidget(QtWidgets.QLabel("Scan Depth:"))
        scan_layout.addWidget(self.editor_widgets['scanDepth_edit'])
        scan_layout.addWidget(QtWidgets.QLabel("Case Sensitive:"))
        scan_layout.addWidget(self.editor_widgets['caseSensitive_combo'])
        scan_layout.addWidget(QtWidgets.QLabel("Whole Words:"))
        scan_layout.addWidget(self.editor_widgets['matchWholeWords_combo'])
        scan_layout.addWidget(QtWidgets.QLabel("Group Scoring:"))
        scan_layout.addWidget(self.editor_widgets['useGroupScoring_combo'])
        editor_right_layout.addWidget(scan_group)
        advanced_group = QtWidgets.QGroupBox("Groups, Timing & Recursion")
        advanced_layout = QtWidgets.QGridLayout(advanced_group)
        advanced_layout.setColumnStretch(1, 1)
        advanced_layout.setColumnStretch(3, 1)
        group_layout = QtWidgets.QHBoxLayout()
        self.editor_widgets['group_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['groupOverride_check'] = QtWidgets.QCheckBox("Prioritize")
        group_layout.addWidget(self.editor_widgets['group_edit'])
        group_layout.addWidget(self.editor_widgets['groupOverride_check'])
        advanced_layout.addWidget(QtWidgets.QLabel("Inclusion Group:"), 0, 0)
        advanced_layout.addLayout(group_layout, 0, 1, 1, 3)
        self.editor_widgets['groupWeight_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['groupWeight_edit'].setValidator(QtGui.QIntValidator())
        self.editor_widgets['sticky_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['sticky_edit'].setValidator(QtGui.QIntValidator())
        self.editor_widgets['cooldown_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['cooldown_edit'].setValidator(QtGui.QIntValidator())
        self.editor_widgets['delay_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['delay_edit'].setValidator(QtGui.QIntValidator())
        numeric_fields_layout = QtWidgets.QHBoxLayout()
        numeric_fields_layout.addWidget(QtWidgets.QLabel("Group Weight:"))
        numeric_fields_layout.addWidget(self.editor_widgets['groupWeight_edit'])
        numeric_fields_layout.addWidget(QtWidgets.QLabel("Sticky:"))
        numeric_fields_layout.addWidget(self.editor_widgets['sticky_edit'])
        numeric_fields_layout.addWidget(QtWidgets.QLabel("Cooldown:"))
        numeric_fields_layout.addWidget(self.editor_widgets['cooldown_edit'])
        numeric_fields_layout.addWidget(QtWidgets.QLabel("Delay:"))
        numeric_fields_layout.addWidget(self.editor_widgets['delay_edit'])
        advanced_layout.addLayout(numeric_fields_layout, 1, 0, 1, 4)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        advanced_layout.addWidget(separator, 2, 0, 1, 4)
        self.editor_widgets['addMemo_check'] = QtWidgets.QCheckBox("Add to context memory (addMemo)")
        self.editor_widgets['preventRecursion_check'] = QtWidgets.QCheckBox("Prevent further recursion")
        self.editor_widgets['excludeRecursion_check'] = QtWidgets.QCheckBox("Non-recursable (will not be activated by another)")
        delay_recursion_layout = QtWidgets.QHBoxLayout()
        self.editor_widgets['delayUntilRecursion_check'] = QtWidgets.QCheckBox("Delay until recursion")
        self.editor_widgets['delayRecursionLevel_edit'] = QtWidgets.QLineEdit()
        self.editor_widgets['delayRecursionLevel_edit'].setPlaceholderText("Level (opt.)")
        self.editor_widgets['delayRecursionLevel_edit'].setValidator(QtGui.QIntValidator(1, 999))
        self.editor_widgets['delayRecursionLevel_edit'].setVisible(False)
        delay_recursion_layout.addWidget(self.editor_widgets['delayUntilRecursion_check'])
        delay_recursion_layout.addWidget(self.editor_widgets['delayRecursionLevel_edit'])
        delay_recursion_layout.addStretch()
        advanced_layout.addWidget(self.editor_widgets['addMemo_check'], 3, 0, 1, 2)
        advanced_layout.addWidget(self.editor_widgets['preventRecursion_check'], 3, 2, 1, 2)
        advanced_layout.addWidget(self.editor_widgets['excludeRecursion_check'], 4, 0, 1, 2)
        advanced_layout.addLayout(delay_recursion_layout, 4, 2, 1, 2)
        def toggle_recursion_level_field(checked):
            self.editor_widgets['delayRecursionLevel_edit'].setVisible(checked)
        self.editor_widgets['delayUntilRecursion_check'].toggled.connect(toggle_recursion_level_field)
        self.editor_widgets['automationId_edit'] = QtWidgets.QLineEdit()
        advanced_layout.addWidget(QtWidgets.QLabel("Automation ID:"), 5, 0)
        advanced_layout.addWidget(self.editor_widgets['automationId_edit'], 5, 1, 1, 3)
        editor_right_layout.addWidget(advanced_group)
        editor_right_layout.addStretch()
        editor_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        editor_splitter.addWidget(editor_left_panel)
        editor_splitter.addWidget(scroll_area)
        editor_splitter.setSizes([400, 700])
        editor_layout.addWidget(editor_splitter)

    def on_file_loaded(self):
        self.editor_refresh_listbox()

    def editor_set_panel_enabled(self, enabled):
            self.editor_form_widget.setEnabled(enabled)

    def editor_clear_form(self):
        for widget in self.editor_widgets.values():
            if isinstance(widget, QtWidgets.QLineEdit): 
                widget.clear()
            elif isinstance(widget, QtWidgets.QTextEdit): 
                widget.clear()
            elif isinstance(widget, QtWidgets.QCheckBox): 
                widget.setChecked(False)
            elif isinstance(widget, QtWidgets.QComboBox): 
                widget.setCurrentIndex(0)
        self.selected_editor_entry_id = None
        self.editor_active_entry_copy = None

    def editor_refresh_listbox(self, search_term=""):
        self.editor_entry_table.blockSignals(True)
        self.editor_entry_table.setRowCount(0)

        sorted_entries = self._get_sorted_lore_entries()
        if not sorted_entries:
            self.editor_entry_table.blockSignals(False)
            return

        entries_to_display = []
        for entry_id, entry_data in sorted_entries:
            uid_str = str(entry_data.get('uid', ''))
            comment_str = entry_data.get('comment', '')
            keywords_list = entry_data.get('key', [])
            keywords_str = ", ".join(keywords_list)

            if not search_term:
                entries_to_display.append((entry_id, entry_data))
            else:
                term_lower = search_term.lower()
                if (term_lower in uid_str.lower() or 
                    term_lower in keywords_str.lower() or 
                    term_lower in comment_str.lower()):
                    entries_to_display.append((entry_id, entry_data))

        self.editor_entry_table.setRowCount(len(entries_to_display))

        for row, (entry_id, entry_data) in enumerate(entries_to_display):
            uid = str(entry_data.get('uid', 'N/A'))
            comment = entry_data.get('comment', '')
            keywords = ", ".join(entry_data.get('key', []))

            uid_item = QtWidgets.QTableWidgetItem(uid)
            uid_item.setData(QtCore.Qt.UserRole, entry_id)

            keywords_item = QtWidgets.QTableWidgetItem(keywords)
            comment_item = QtWidgets.QTableWidgetItem(comment)
            
            self.editor_entry_table.setItem(row, 0, uid_item)
            self.editor_entry_table.setItem(row, 1, keywords_item)
            self.editor_entry_table.setItem(row, 2, comment_item)

        self.editor_entry_table.resizeColumnsToContents()
        if self.editor_entry_table.columnWidth(0) < 60:
            self.editor_entry_table.setColumnWidth(0, 60)
        self.editor_entry_table.blockSignals(False)

    @QtCore.Slot()
    def editor_load_entry_details(self):
        self.editor_debounce_timer.stop()
        selected_row = self.editor_entry_table.currentRow()
        if selected_row < 0:
            self.editor_clear_form()
            self.editor_set_panel_enabled(False)
            return
        uid_item = self.editor_entry_table.item(selected_row, 0)
        if not uid_item:
            return
        entry_id = uid_item.data(QtCore.Qt.UserRole)
        if not self.main_window.data or 'entries' not in self.main_window.data or entry_id not in self.main_window.data['entries']:
            return
        if self.is_saving_from_editor and self.selected_editor_entry_id == entry_id:
            return

        self.selected_editor_entry_id = entry_id
        self.editor_active_entry_copy = copy.deepcopy(self.main_window.data['entries'][entry_id])
        entry = self.editor_active_entry_copy

        def set_tri_state_combo(widget, value):
            if value is None:
                widget.setCurrentIndex(0)
            elif value is True: 
                widget.setCurrentIndex(1)
            else: 
                widget.setCurrentIndex(2)

        def set_numeric_field(widget, value, default=0):
            if value is None or value == default: 
                widget.setText("")
            else: 
                widget.setText(str(value))

        focused_widget = QtWidgets.QApplication.focusWidget()

        for widget in self.editor_widgets.values():
            widget.blockSignals(True)

        def safe_update(widget, update_func):
            if not (self.is_saving_from_editor and widget is focused_widget):
                update_func()

        safe_update(self.editor_widgets['enabled_check'], lambda: self.editor_widgets['enabled_check'].setChecked(not entry.get('disable', False)))
        safe_update(self.editor_widgets['comment_edit'], lambda: self.editor_widgets['comment_edit'].setText(entry.get('comment', '')))
        safe_update(self.editor_widgets['keys_edit'], lambda: self.editor_widgets['keys_edit'].setText(", ".join(entry.get('key', []))))
        safe_update(self.editor_widgets['keysecondary_edit'], lambda: self.editor_widgets['keysecondary_edit'].setText(", ".join(entry.get('keysecondary', []))))
        safe_update(self.editor_widgets['content_edit'], lambda: self.editor_widgets['content_edit'].setPlainText(entry.get('content', '')))

        safe_update(self.editor_widgets['logic_combo'], lambda: self.editor_widgets['logic_combo'].setCurrentIndex(entry.get('selectiveLogic', 0)))
        safe_update(self.editor_widgets['position_combo'], lambda: self.editor_widgets['position_combo'].setCurrentIndex(entry.get('position', 0)))
        
        strategy_idx = 1 if entry.get('constant') else 2 if entry.get('vectorized') else 0
        safe_update(self.editor_widgets['strategy_combo'], lambda: self.editor_widgets['strategy_combo'].setCurrentIndex(strategy_idx))
        
        safe_update(self.editor_widgets['order_edit'], lambda: self.editor_widgets['order_edit'].setText(str(entry.get('order', 100))))
        safe_update(self.editor_widgets['depth_edit'], lambda: set_numeric_field(self.editor_widgets['depth_edit'], entry.get('depth'), default=None))
        safe_update(self.editor_widgets['probability_edit'], lambda: self.editor_widgets['probability_edit'].setText(str(entry.get('probability', 100))))
        safe_update(self.editor_widgets['useProbability_check'], lambda: self.editor_widgets['useProbability_check'].setChecked(entry.get('useProbability', True)))

        safe_update(self.editor_widgets['scanDepth_edit'], lambda: set_numeric_field(self.editor_widgets['scanDepth_edit'], entry.get('scanDepth'), default=None))
        safe_update(self.editor_widgets['caseSensitive_combo'], lambda: set_tri_state_combo(self.editor_widgets['caseSensitive_combo'], entry.get('caseSensitive')))
        safe_update(self.editor_widgets['matchWholeWords_combo'], lambda: set_tri_state_combo(self.editor_widgets['matchWholeWords_combo'], entry.get('matchWholeWords')))
        safe_update(self.editor_widgets['useGroupScoring_combo'], lambda: set_tri_state_combo(self.editor_widgets['useGroupScoring_combo'], entry.get('useGroupScoring')))

        safe_update(self.editor_widgets['group_edit'], lambda: self.editor_widgets['group_edit'].setText(entry.get('group', '')))
        safe_update(self.editor_widgets['groupOverride_check'], lambda: self.editor_widgets['groupOverride_check'].setChecked(entry.get('groupOverride', False)))
        
        group_weight_value = entry.get('groupWeight', 100)
        safe_update(self.editor_widgets['groupWeight_edit'], lambda: self.editor_widgets['groupWeight_edit'].setText(str(group_weight_value)))
        
        safe_update(self.editor_widgets['sticky_edit'], lambda: set_numeric_field(self.editor_widgets['sticky_edit'], entry.get('sticky'), default=0))
        safe_update(self.editor_widgets['cooldown_edit'], lambda: set_numeric_field(self.editor_widgets['cooldown_edit'], entry.get('cooldown'), default=0))
        safe_update(self.editor_widgets['delay_edit'], lambda: set_numeric_field(self.editor_widgets['delay_edit'], entry.get('delay'), default=0))
        
        safe_update(self.editor_widgets['addMemo_check'], lambda: self.editor_widgets['addMemo_check'].setChecked(entry.get('addMemo', True)))
        safe_update(self.editor_widgets['preventRecursion_check'], lambda: self.editor_widgets['preventRecursion_check'].setChecked(entry.get('preventRecursion', False)))
        safe_update(self.editor_widgets['excludeRecursion_check'], lambda: self.editor_widgets['excludeRecursion_check'].setChecked(entry.get('excludeRecursion', False)))
        
        delay_value = entry.get('delayUntilRecursion', False)
        is_delayed = bool(delay_value)
        safe_update(self.editor_widgets['delayUntilRecursion_check'], lambda: self.editor_widgets['delayUntilRecursion_check'].setChecked(is_delayed))

        def update_delay_recursion_level():
            self.editor_widgets['delayRecursionLevel_edit'].setVisible(is_delayed)
            if isinstance(delay_value, int) and delay_value > 1:
                self.editor_widgets['delayRecursionLevel_edit'].setText(str(delay_value))
            else:
                self.editor_widgets['delayRecursionLevel_edit'].clear()
        safe_update(self.editor_widgets['delayRecursionLevel_edit'], update_delay_recursion_level)
        
        safe_update(self.editor_widgets['automationId_edit'], lambda: self.editor_widgets['automationId_edit'].setText(entry.get('automationId', '')))

        for widget in self.editor_widgets.values():
            widget.blockSignals(False)

        current_pos_index = self.editor_widgets['position_combo'].currentIndex()
        self._update_insertion_depth_visibility(current_pos_index)
        
        self.editor_set_panel_enabled(True)
        self.editor_save_status_label.setText("<b>Saved ✅</b>")
        logger.debug(f"Loaded entry '{entry_id}' fully into editor form.")

    def get_int_or_default(self, widget, default_val):
        text = widget.text().strip()
        if not text:
            return default_val
        try:
            return int(text)
        except (ValueError, TypeError):
            return default_val

    @QtCore.Slot()
    def editor_save_entry_changes(self):
        if not self.selected_editor_entry_id or self.editor_active_entry_copy is None:
            return
        self.editor_debounce_timer.stop()

        self.main_window.set_dirty_flag()
        
        self.is_saving_from_editor = True
        try:
            entry = self.editor_active_entry_copy

            def get_tri_state_value(widget):
                idx = widget.currentIndex()
                if idx == 0: 
                    return None
                return idx == 1

            entry['disable'] = not self.editor_widgets['enabled_check'].isChecked()
            entry['comment'] = self.editor_widgets['comment_edit'].text().strip()
            entry['key'] = [k.strip() for k in self.editor_widgets['keys_edit'].text().split(',') if k.strip()]
            entry['keysecondary'] = [k.strip() for k in self.editor_widgets['keysecondary_edit'].text().split(',') if k.strip()]
            entry['content'] = self.editor_widgets['content_edit'].toPlainText()

            entry['selectiveLogic'] = self.editor_widgets['logic_combo'].currentIndex()
            entry['position'] = self.editor_widgets['position_combo'].currentIndex()
            strategy_idx = self.editor_widgets['strategy_combo'].currentIndex()
            entry['constant'] = (strategy_idx == 1)
            entry['vectorized'] = (strategy_idx == 2)
            entry['order'] = self.get_int_or_default(self.editor_widgets['order_edit'], 100)
            
            entry['depth'] = self.get_int_or_default(self.editor_widgets['depth_edit'], None)
            
            entry['probability'] = self.get_int_or_default(self.editor_widgets['probability_edit'], 100)
            entry['useProbability'] = self.editor_widgets['useProbability_check'].isChecked()

            entry['scanDepth'] = self.get_int_or_default(self.editor_widgets['scanDepth_edit'], None)
            entry['caseSensitive'] = get_tri_state_value(self.editor_widgets['caseSensitive_combo'])
            entry['matchWholeWords'] = get_tri_state_value(self.editor_widgets['matchWholeWords_combo'])
            entry['useGroupScoring'] = get_tri_state_value(self.editor_widgets['useGroupScoring_combo'])

            entry['group'] = self.editor_widgets['group_edit'].text().strip()
            entry['groupOverride'] = self.editor_widgets['groupOverride_check'].isChecked()
            entry['groupWeight'] = self.get_int_or_default(self.editor_widgets['groupWeight_edit'], 100)
            entry['sticky'] = self.get_int_or_default(self.editor_widgets['sticky_edit'], 0)
            entry['cooldown'] = self.get_int_or_default(self.editor_widgets['cooldown_edit'], 0)
            entry['delay'] = self.get_int_or_default(self.editor_widgets['delay_edit'], 0)
            entry['addMemo'] = self.editor_widgets['addMemo_check'].isChecked()
            entry['preventRecursion'] = self.editor_widgets['preventRecursion_check'].isChecked()
            entry['excludeRecursion'] = self.editor_widgets['excludeRecursion_check'].isChecked()
            
            if not self.editor_widgets['delayUntilRecursion_check'].isChecked():
                entry['delayUntilRecursion'] = False
            else:
                level_text = self.editor_widgets['delayRecursionLevel_edit'].text().strip()
                if level_text.isdigit():
                    entry['delayUntilRecursion'] = int(level_text)
                else:
                    entry['delayUntilRecursion'] = True
            
            entry['automationId'] = self.editor_widgets['automationId_edit'].text().strip()

            keys_to_check_for_null = ['scanDepth', 'depth', 'caseSensitive', 'matchWholeWords', 'useGroupScoring']
            for key in keys_to_check_for_null:
                if entry.get(key) is None and key in entry:
                    del entry[key]

            self.main_window.data['entries'][self.selected_editor_entry_id] = self.editor_active_entry_copy
            
            logger.debug(f"Applied changes for entry ID '{self.selected_editor_entry_id}' to in-memory data.")
            self.editor_save_status_label.setText("<b>Applied ✅</b>")

            id_to_reselect = self.selected_editor_entry_id

            self.editor_refresh_listbox(self.editor_search_input.text())
            self.main_window.translation_tab.populate_table_data()

            if id_to_reselect:
                self._select_entry_in_list_by_uid(id_to_reselect)
        finally:
            self.is_saving_from_editor = False

    @QtCore.Slot()
    def editor_add_entry(self):
        if not self.main_window.data: 
            QtWidgets.QMessageBox.warning(self, "Action Failed", "Please load or create a LORE-book before adding entries.")
            return

        new_uid = self._get_free_uid()

        new_entry = {
                    "uid": new_uid, "key": [], "keysecondary": [], "comment": "New Entry", "content": "",
                    "constant": False, "vectorized": False, "selective": True, "selectiveLogic": 0,
                    "addMemo": True, "order": 100, "position": 0, "disable": False, "excludeRecursion": False,
                    "preventRecursion": False, "delayUntilRecursion": False, "matchPersonaDescription": False,
                    "matchCharacterDescription": False, "matchCharacterPersonality": False,
                    "matchCharacterDepthPrompt": False, "matchScenario": False, "matchCreatorNotes": False,
                    "probability": 100, "useProbability": True, "depth": 4, "group": "", "groupOverride": False,
                    "groupWeight": 100, "scanDepth": None, "caseSensitive": None, "matchWholeWords": None,
                    "useGroupScoring": None, "automationId": "", "role": None, "sticky": None,
                    "cooldown": None, "delay": None
                }
        
        self.main_window.data['entries'][str(new_uid)] = new_entry
        logger.info(f"Added new entry with UID: {new_uid}")
        
        self.main_window.set_dirty_flag()

        self.editor_refresh_listbox(self.editor_search_input.text())
        self.main_window.translation_tab.populate_table_data()

        self._select_entry_in_list_by_uid(new_uid)

    @QtCore.Slot()
    def editor_delete_entry(self):
        if not self.selected_editor_entry_id:
            QtWidgets.QMessageBox.warning(self, "Action Failed", "Please select an entry to delete.")
            return

        entry_name = self.main_window.data['entries'][self.selected_editor_entry_id].get('comment', self.selected_editor_entry_id)
        reply = QtWidgets.QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to permanently delete the entry '{entry_name}'?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            row_to_delete = self.editor_entry_table.currentRow()

            del self.main_window.data['entries'][self.selected_editor_entry_id]
            logger.info(f"Deleted entry ID: {self.selected_editor_entry_id}")
            
            self.main_window.set_dirty_flag()

            self.editor_clear_form()
            self.editor_set_panel_enabled(False)

            self.editor_refresh_listbox(self.editor_search_input.text())
            self.main_window.translation_tab.populate_table_data()

            new_row_count = self.editor_entry_table.rowCount()
            if new_row_count > 0:
                index_to_select = min(row_to_delete, new_row_count - 1)
                self.editor_entry_table.setCurrentCell(index_to_select, 0)

    @QtCore.Slot(str)
    def on_global_search_changed(self, text):
        self.editor_refresh_listbox(text)
        self.search_term_changed.emit(text)

    def _get_sorted_lore_entries(self):
        if not self.main_window.data or 'entries' not in self.main_window.data:
            return []

        entries = self.main_window.data.get('entries', {})

        def sort_key(item):
            try:
                return int(item[1].get('uid', 0))
            except (ValueError, TypeError):
                return 0
        
        sorted_entries = sorted(entries.items(), key=sort_key)
        return sorted_entries

    def _get_free_uid(self):
        if not self.main_window.data or 'entries' not in self.main_window.data:
            return 0
        all_uids = [int(entry.get('uid', -1)) for entry in self.main_window.data['entries'].values() if isinstance(entry, dict) and str(entry.get('uid')).isdigit()]
        if not all_uids:
            return 0
        return max(all_uids) + 1

    def _select_entry_in_list_by_uid(self, uid_to_select):
        for row in range(self.editor_entry_table.rowCount()):
            item = self.editor_entry_table.item(row, 0)
            if item and item.text() == str(uid_to_select):
                self.editor_entry_table.setCurrentCell(row, 0)
                self.editor_entry_table.scrollToItem(item, QtWidgets.QAbstractItemView.ScrollHint.PositionAtCenter)
                break

    @QtCore.Slot()
    def editor_duplicate_entry(self):
        if not self.selected_editor_entry_id:
            QtWidgets.QMessageBox.warning(self, "Action Failed", "Please select an entry to duplicate.")
            return

        original_entry = copy.deepcopy(self.main_window.data['entries'][self.selected_editor_entry_id])
        
        new_uid = self._get_free_uid()

        new_entry = original_entry
        new_entry['uid'] = new_uid
        new_entry['comment'] = f"{original_entry.get('comment', 'Entry')} (Copy)"

        self.main_window.data['entries'][str(new_uid)] = new_entry
        logger.info(f"Duplicated entry {self.selected_editor_entry_id} to new entry with UID: {new_uid}")
        
        self.main_window.set_dirty_flag()

        self.editor_refresh_listbox(self.editor_search_input.text())
        self.main_window.translation_tab.populate_table_data()

        self._select_entry_in_list_by_uid(new_uid)

    @QtCore.Slot(int)
    def _update_insertion_depth_visibility(self, index):
        is_directive_position = index in [6, 7, 8]
        
        if 'depth_edit' in self.editor_widgets:
            self.editor_widgets['depth_edit'].setVisible(is_directive_position)

    @QtCore.Slot()
    def _trigger_editor_debounce_save(self):
        if self.selected_editor_entry_id is not None:
            self.editor_save_status_label.setText("<i>Changes detected...</i>")
            self.editor_debounce_timer.start()

    def _create_debounce_timer(self, slot_function, interval=1000):
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(slot_function)
        return timer

    @QtCore.Slot()
    def force_save_entry_changes(self):
        if self.editor_debounce_timer.isActive():
            self.editor_debounce_timer.stop()
        self.editor_save_entry_changes()

class TranslationTab(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window

        self.table_data = []
        self.current_row = None
        self.current_orig_key_for_editor = None
        self.current_translation_in_editor_before_change = None
        self.current_target_language = current_settings.get("selected_target_language", "")
        self.current_source_language = current_settings.get("selected_source_language", default_settings["available_source_languages"][0])

        self.translator_debounce_timer = self._create_debounce_timer(self.apply_edited_translation)

        self.init_ui()
        self._update_target_language_combo()
        self._update_source_language_combo()

    def init_ui(self):
        translation_layout = QtWidgets.QVBoxLayout(self)

        language_panel_layout = QtWidgets.QHBoxLayout()
        source_lang_group = QtWidgets.QGroupBox("LORE-book Language")
        source_lang_layout = QtWidgets.QHBoxLayout(source_lang_group)
        self.source_lang_combo = QtWidgets.QComboBox()
        self.source_lang_combo.currentTextChanged.connect(self.on_source_language_change)
        manage_source_langs_button = QtWidgets.QPushButton("Manage")
        manage_source_langs_button.clicked.connect(self.open_manage_source_languages_dialog)
        source_lang_layout.addWidget(manage_source_langs_button)
        source_lang_layout.addWidget(self.source_lang_combo)
        language_panel_layout.addWidget(source_lang_group, stretch=1)
        target_lang_group = QtWidgets.QGroupBox("Language for Translation")
        target_lang_layout = QtWidgets.QHBoxLayout(target_lang_group)
        self.target_lang_combo = QtWidgets.QComboBox()
        self.target_lang_combo.currentTextChanged.connect(self.on_target_language_change)
        manage_target_langs_button = QtWidgets.QPushButton("Manage")
        manage_target_langs_button.clicked.connect(self.open_manage_target_languages_dialog)
        target_lang_layout.addWidget(self.target_lang_combo)
        target_lang_layout.addWidget(manage_target_langs_button)
        language_panel_layout.addWidget(target_lang_group, stretch=1)
        translation_layout.addLayout(language_panel_layout)

        middle_v_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Vertical)
        middle_v_splitter.setOpaqueResize(False)
        top_middle_h_splitter = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        top_middle_h_splitter.setOpaqueResize(False)
        table_group = QtWidgets.QGroupBox("LORE Entries")
        table_layout = QtWidgets.QVBoxLayout(table_group)
        self.translation_search_input = QtWidgets.QLineEdit()
        self.translation_search_input.setPlaceholderText("Search UID, Original/Translated Key, Content...")
        self.translation_search_input.textChanged.connect(self.filter_translation_table)
        table_layout.addWidget(self.translation_search_input)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['UID', 'Original Key', f'Translated ({self.current_target_language if self.current_target_language else "N/A"})', 'Content Preview'])
        self.table.cellClicked.connect(self.on_cell_click)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setWordWrap(False)
        table_layout.addWidget(self.table)
        top_middle_h_splitter.addWidget(table_group)
        edit_group = QtWidgets.QGroupBox("Edit Selected Translation")
        edit_layout = QtWidgets.QFormLayout(edit_group)
        orig_key_layout = QtWidgets.QHBoxLayout()
        orig_key_layout.setContentsMargins(0, 0, 0, 0)
        self.orig_label = QtWidgets.QLabel('')
        self.orig_label.setWordWrap(True)
        orig_key_layout.addWidget(self.orig_label)
        orig_key_layout.addStretch(1)
        self.translator_save_status_label = QtWidgets.QLabel("<i>No entry selected</i>")
        self.translator_save_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        orig_key_layout.addWidget(self.translator_save_status_label)
        edit_layout.addRow('Original Key:', orig_key_layout)

        self.trans_edit_label = QtWidgets.QLabel(f'Translation ({self.current_target_language if self.current_target_language else "N/A"}):')
        self.trans_edit = QtWidgets.QLineEdit()
        self.trans_edit.setPlaceholderText("Edit or enter translation here")
        self.trans_edit.textChanged.connect(self._trigger_translator_debounce_save)
        self.trans_edit.editingFinished.connect(self.force_apply_edit)
        edit_layout.addRow(self.trans_edit_label, self.trans_edit)

        edit_buttons_layout = QtWidgets.QHBoxLayout()
        self.regenerate_btn = QtWidgets.QPushButton('Regenerate')
        self.regenerate_btn.clicked.connect(self.regenerate_selected_translation_action)
        self.delete_selected_translations_btn = QtWidgets.QPushButton('Delete Selected')
        self.delete_selected_translations_btn.setToolTip("Delete selected lines \nTo delete all lines, press Ctrl + A and click this button.")
        self.delete_selected_translations_btn.clicked.connect(self.delete_selected_translations_action)
        edit_buttons_layout.addWidget(self.regenerate_btn)
        edit_buttons_layout.addWidget(self.delete_selected_translations_btn)
        edit_layout.addRow(edit_buttons_layout)
        batch_operations_layout = QtWidgets.QHBoxLayout()
        trans_sel_btn = QtWidgets.QPushButton('Translate Selected')
        trans_sel_btn.clicked.connect(self.translate_selected_rows_action)
        trans_all_btn = QtWidgets.QPushButton('Translate All')
        trans_all_btn.clicked.connect(self.translate_all_action)
        batch_operations_layout.addWidget(trans_sel_btn)
        batch_operations_layout.addWidget(trans_all_btn)
        edit_layout.addRow(batch_operations_layout)
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        edit_layout.addRow(separator)
        self.useContentContextCheck = QtWidgets.QCheckBox("Use LORE «content» as context")
        self.useContentContextCheck.setChecked(current_settings.get("use_content_as_context", True))
        self.useContentContextCheck.setToolTip("Use the «content» field from the LORE entry as context for translation.\n(Improves translation quality.\nIf the response is empty, disable this)")
        self.useContentContextCheck.toggled.connect(self.on_toggle_use_context)
        edit_layout.addRow(self.useContentContextCheck)

        thinking_controls_layout = QtWidgets.QHBoxLayout()
        self.enableModelThinkingCheck = QtWidgets.QCheckBox("Enable Model Thinking")
        self.enableModelThinkingCheck.setToolTip("Enable model thinking to improve translation quality for complex terms.\nUnchecking this disables the feature (sets budget to 0).")
        
        self.thinking_widget_container = QtWidgets.QWidget()
        thinking_slider_layout = QtWidgets.QHBoxLayout(self.thinking_widget_container)
        thinking_slider_layout.setContentsMargins(0, 0, 0, 0)
        
        thinking_label = QtWidgets.QLabel("Thinking Budget:")
        self.thinking_budget_slider = QtWidgets.QSlider(QtCore.Qt.Orientation.Horizontal)
        self.thinking_budget_slider.setSingleStep(1)
        
        self.thinking_budget_label = QtWidgets.QLineEdit()
        self.thinking_budget_label.setReadOnly(True)
        self.thinking_budget_label.setFixedWidth(70)
        self.thinking_budget_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        thinking_slider_layout.addWidget(thinking_label)
        thinking_slider_layout.addWidget(self.thinking_budget_slider, 1)
        thinking_slider_layout.addWidget(self.thinking_budget_label)

        thinking_controls_layout.addWidget(self.enableModelThinkingCheck)
        thinking_controls_layout.addWidget(self.thinking_widget_container, 1)
        edit_layout.addRow(thinking_controls_layout)

        self.possible_budget_values = []

        self.enableModelThinkingCheck.toggled.connect(self.on_toggle_enable_thinking)
        self.thinking_budget_slider.valueChanged.connect(self.on_slider_value_changed)
        self.thinking_budget_slider.sliderReleased.connect(self.on_slider_released)
        
        self.update_model_specific_ui()

        self.rpm_status_label = QtWidgets.QLabel("RPM: Initializing...")
        self.rpm_status_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.rpm_status_label.setStyleSheet("QLabel { color : green; font-weight: bold; }")
        self.rpm_status_label.setToolTip("API Requests Per Minute status. Helps avoid rate limits.")
        edit_layout.addRow(self.rpm_status_label)
        top_middle_h_splitter.addWidget(edit_group)
        top_middle_h_splitter.setStretchFactor(0, 2)
        top_middle_h_splitter.setStretchFactor(1, 1)
        middle_v_splitter.addWidget(top_middle_h_splitter)
        content_display_group = QtWidgets.QGroupBox("Full Content")
        content_display_layout = QtWidgets.QVBoxLayout(content_display_group)
        self.full_content_display = QtWidgets.QTextEdit()
        self.full_content_display.setReadOnly(True)
        content_display_layout.addWidget(self.full_content_display)
        middle_v_splitter.addWidget(content_display_group)
        translation_layout.addWidget(middle_v_splitter, stretch=2)

        self.log_panel = QtWidgets.QGroupBox("Application Log")
        log_panel_layout = QtWidgets.QVBoxLayout(self.log_panel)
        self.log_text_edit = QtWidgets.QTextEdit()
        self.log_text_edit.setReadOnly(True)
        log_panel_layout.addWidget(self.log_text_edit)
        self.log_panel.setVisible(current_settings.get("show_log_panel", True)) 
        translation_layout.addWidget(self.log_panel, stretch=1)

    def on_file_loaded(self):
        self.populate_table_data()

    def set_log_panel_visibility(self, visible):
        self.log_panel.setVisible(visible)

    def get_log_text_edit(self):
        return self.log_text_edit

    @QtCore.Slot(bool)
    def on_toggle_use_context(self, checked):
        current_settings["use_content_as_context"] = checked
        logger.info(f"'Use LORE content as context' set to: {checked}")
        save_settings()

    @QtCore.Slot(bool)
    def on_toggle_enable_thinking(self, checked):
        self.thinking_widget_container.setVisible(checked)
        current_settings["enable_model_thinking"] = checked
        
        if not checked:
            current_settings["thinking_budget_value"] = 0
        else:
            self.update_thinking_budget_from_slider()
        
        logger.info(f"'Enable Model Thinking' set to: {checked}. Effective budget: {current_settings['thinking_budget_value']}")
        save_settings()


    @QtCore.Slot(int)
    def on_slider_value_changed(self, slider_index):
        if not self.possible_budget_values or slider_index >= len(self.possible_budget_values):
            return
        
        value = self.possible_budget_values[slider_index]
        self.thinking_budget_label.setText("Dynamic" if value == -1 else str(value))

    @QtCore.Slot()
    def on_slider_released(self):
        self.update_thinking_budget_from_slider()
        logger.info(f"Thinking budget set to: {current_settings['thinking_budget_value']}")
        save_settings()

    def update_thinking_budget_from_slider(self):
        slider_index = self.thinking_budget_slider.value()
        if self.possible_budget_values and slider_index < len(self.possible_budget_values):
            current_settings['thinking_budget_value'] = self.possible_budget_values[slider_index]

    def update_model_specific_ui(self):
        model_name = current_settings.get("gemini_model", "").lower()
        
        is_pro = "pro" in model_name
        is_flash = "flash" in model_name

        if not is_pro and not is_flash:
            self.enableModelThinkingCheck.setVisible(False)
            self.thinking_widget_container.setVisible(False)
            return
        
        self.enableModelThinkingCheck.setVisible(True)
        max_budget = 32768 if is_pro else 24576

        self.possible_budget_values = [-1] + list(range(512, max_budget + 1, 512))
        self.thinking_budget_slider.setRange(0, len(self.possible_budget_values) - 1)

        if is_pro:
            self.enableModelThinkingCheck.setChecked(True)
            self.enableModelThinkingCheck.setEnabled(False)
        else:
            self.enableModelThinkingCheck.setEnabled(True)
            self.enableModelThinkingCheck.setChecked(current_settings.get("enable_model_thinking", True))

        budget_value = current_settings.get("thinking_budget_value", -1)
        if current_settings.get("enable_model_thinking") is False:
            budget_value = 0

        try:
            target_index = self.possible_budget_values.index(budget_value)
        except ValueError:
            target_index = 0 
            current_settings['thinking_budget_value'] = -1

        self.thinking_budget_slider.setValue(target_index)
        self.on_slider_value_changed(target_index)

        self.thinking_widget_container.setVisible(self.enableModelThinkingCheck.isChecked())

    def _update_target_language_combo(self):
        self.target_lang_combo.blockSignals(True)
        self.target_lang_combo.clear()
        stored_target_langs = current_settings.get("target_languages", [])

        if stored_target_langs:
            self.target_lang_combo.addItems(stored_target_langs)
            selected_lang = current_settings.get("selected_target_language", "")
            if selected_lang and selected_lang in stored_target_langs:
                self.target_lang_combo.setCurrentText(selected_lang)
            elif stored_target_langs:
                self.target_lang_combo.setCurrentIndex(0)
                current_settings["selected_target_language"] = stored_target_langs[0]
        else:
            self.target_lang_combo.setPlaceholderText("No target languages")
            current_settings["selected_target_language"] = ""
        self.target_lang_combo.blockSignals(False)
        self.on_target_language_change(self.target_lang_combo.currentText())

    def _update_source_language_combo(self):
        self.source_lang_combo.blockSignals(True)
        self.source_lang_combo.clear()

        available_source_langs = current_settings.get("available_source_languages", [default_settings["available_source_languages"][0]])
        if not available_source_langs:
            available_source_langs = ["English"]
        current_settings["available_source_languages"] = available_source_langs
        self.source_lang_combo.addItems(available_source_langs)

        selected_source = current_settings.get("selected_source_language", "")
        if selected_source and selected_source in available_source_langs: 
            self.source_lang_combo.setCurrentText(selected_source)
        elif available_source_langs: 
            self.source_lang_combo.setCurrentIndex(0)
            current_settings["selected_source_language"] = available_source_langs[0]
        self.source_lang_combo.blockSignals(False)
        self.on_source_language_change(self.source_lang_combo.currentText())

    def open_manage_target_languages_dialog(self):
        current_langs = current_settings.get("target_languages", [])
        dialog = ManageLanguagesDialog(current_langs, "Target", self)

        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_langs = dialog.get_languages()
            current_settings["target_languages"] = new_langs
            logger.info(f"Target languages updated: {new_langs}")
            selected_target_lang = current_settings.get("selected_target_language", "")
            if new_langs and selected_target_lang not in new_langs:
                current_settings["selected_target_language"] = new_langs[0]
            elif not new_langs:
                current_settings["selected_target_language"] = ""
            self._update_target_language_combo()
            save_settings()

    def open_manage_source_languages_dialog(self):
        current_langs = current_settings.get("available_source_languages", [])
        dialog = ManageLanguagesDialog(current_langs, "Source", self)

        if dialog.exec() == QtWidgets.QDialog.Accepted:
            new_langs = dialog.get_languages()
            if not new_langs:
                new_langs = ["English"]
                QtWidgets.QMessageBox.information(self, "Defaulting Source Language", "Source languages defaulted to «English».")
            current_settings["available_source_languages"] = new_langs
            logger.info(f"Available source languages updated: {new_langs}")
            selected_source_lang = current_settings.get("selected_source_language", "")
            if selected_source_lang not in new_langs:
                current_settings["selected_source_language"] = new_langs[0]
            self._update_source_language_combo()
            save_settings()

    def on_target_language_change(self, lang_name):
        if self.main_window.active_translation_jobs > 0 and lang_name != self.current_target_language :
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot change target language while translations active.")
            self.target_lang_combo.blockSignals(True)
            self.target_lang_combo.setCurrentText(self.current_target_language if self.current_target_language else "")
            self.target_lang_combo.blockSignals(False)
            return
        self.current_target_language = lang_name if lang_name else ""
        current_settings["selected_target_language"] = self.current_target_language
        logger.debug(f"Target language changed to: {self.current_target_language or 'None'}")
        hdr_text = f'Translated ({self.current_target_language if self.current_target_language else "N/A"})'
        hdr = self.table.horizontalHeaderItem(2)

        if hdr: 
            hdr.setText(hdr_text)
        else: 
            self.table.setHorizontalHeaderLabels(['UID', 'Original Key', hdr_text, 'Content Preview'])
        if hasattr(self, 'trans_edit_label'): 
            self.trans_edit_label.setText(f'Translation ({self.current_target_language if self.current_target_language else "N/A"}):')
        self.orig_label.clear()
        self.trans_edit.clear()
        self.full_content_display.clear()
        self.current_row = None
        self.current_orig_key_for_editor = None
        self.current_translation_in_editor_before_change = None
        self.table.clearSelection()
        if self.main_window.data:
            self.populate_table_data()
        self.main_window.status_bar.showMessage(f"Target language: {self.current_target_language if self.current_target_language else 'None'}")
        save_settings()

    def on_source_language_change(self, lang_name):
        if self.main_window.active_translation_jobs > 0 and lang_name != self.current_source_language:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot change source language while translations active.")
            self.source_lang_combo.blockSignals(True)
            self.source_lang_combo.setCurrentText(self.current_source_language)
            self.source_lang_combo.blockSignals(False)
            return
        self.current_source_language = lang_name if lang_name else default_settings["available_source_languages"][0]
        current_settings["selected_source_language"] = self.current_source_language
        logger.info(f"Source language changed to: {self.current_source_language}")
        self.main_window.status_bar.showMessage(f"LORE-book source language: {self.current_source_language}")
        save_settings()
        if self.main_window.data:
            self.populate_table_data()
    
    def populate_table_data(self):
        sorted_entries = self.main_window.editor_tab._get_sorted_lore_entries()
        if not sorted_entries:
            self.table_data.clear()
            self.update_table_widget()
            return
            
        new_table_data = []
        tgt_lang = self.current_target_language
        src_lang = self.current_source_language
        
        if not src_lang:
            logger.error("Cannot populate table: LORE source lang not set.")
            self.table_data.clear()
            self.update_table_widget()
            return
        for entry_key, entry_data in sorted_entries:
            uid = entry_data.get('uid')
            if uid is None:
                logger.warning(f"Entry '{entry_key}' missing 'uid'. Skipping.")
                continue
            
            uid_str = str(uid)
            original_keys = entry_data.get('key', [])
            content = entry_data.get('content', '')

            if not isinstance(original_keys, list):
                logger.warning(f"Entry UID {uid_str} 'key' field is not a list. Skipping.")
                continue

            if original_keys:
                for orig_key_text in original_keys:
                    orig_key_disp = str(orig_key_text).strip()
                    if not orig_key_disp:
                        continue
                    cache_key = self.main_window._generate_cache_key(uid_str, orig_key_disp, src_lang, tgt_lang)
                    cached_trans = str(self.main_window.cache.get(cache_key, "")).strip() if tgt_lang else ""
                    new_table_data.append([uid_str, orig_key_disp, cached_trans, content])
            else:
                logger.debug(f"Entry UID {uid_str} has an empty 'key' list. Displaying with a blank key.")
                new_table_data.append([uid_str, "", "", content])

        self.table_data = new_table_data
        logger.debug(f"Populated table: {len(self.table_data)} rows for target '{tgt_lang or 'N/A'}'.")
        self.update_table_widget()

    def update_table_widget(self):
        self.table.setRowCount(0)
        tgt_lang_header = self.current_target_language
        header_lbl = f'Translated ({tgt_lang_header if tgt_lang_header else "N/A"})'
        self.table.setHorizontalHeaderLabels(['UID', 'Original Key', header_lbl, 'Content Preview'])
        if not self.table_data:
            return
        self.table.setRowCount(len(self.table_data))
        try:
            self.table.setUpdatesEnabled(False)
            for r, row_content in enumerate(self.table_data):
                if len(row_content) == 4:
                    uid, orig, trans, content = row_content
                    self.table.setItem(r, 0, QtWidgets.QTableWidgetItem(uid))
                    self.table.setItem(r, 1, QtWidgets.QTableWidgetItem(orig))
                    self.table.setItem(r, 2, QtWidgets.QTableWidgetItem(trans))
                    preview = str(content).replace("\n", " ")[:147] + "..." if len(str(content).replace("\n", " ")) > 150 else str(content).replace("\n", " ")
                    self.table.setItem(r, 3, QtWidgets.QTableWidgetItem(preview))
                else:
                    logger.warning(f"Row {r} table_data bad format: {row_content}.")
        finally:
            self.table.setUpdatesEnabled(True)
        header = self.table.horizontalHeader()
        for i in range(4):
            header.setSectionResizeMode(i, QtWidgets.QHeaderView.ResizeMode.Interactive)
        self.table.resizeColumnsToContents()
        header.setMinimumSectionSize(50)
        if self.table.columnWidth(0) < 60:
            self.table.setColumnWidth(0,60)
        if self.table.columnWidth(1) < 150:
            self.table.setColumnWidth(1,150)
        if self.table.columnWidth(2) < 150:
            self.table.setColumnWidth(2,150)
        prev_w = self.table.columnWidth(3)
        if prev_w < 150:
            self.table.setColumnWidth(3, 150)
        elif prev_w > 300:
            self.table.setColumnWidth(3, 300)

    def on_cell_click(self, row, column):
        self.translator_debounce_timer.stop()

        if self.main_window.active_translation_jobs > 0:
            logger.debug("Cell click ignored during active jobs.")
            self.table.clearSelection()
            return
        if not (0 <= row < len(self.table_data)):
            logger.warning(f"Cell click row {row} out of bounds. Clearing editor.")
            self.orig_label.clear()
            self.trans_edit.clear()
            self.full_content_display.clear()
            self.current_row = None
            self.current_orig_key_for_editor = None
            self.current_translation_in_editor_before_change = None
            self.table.clearSelection()
            return
        self.current_row = row
        _uid, orig_k, trans_k, content_k = self.table_data[row]
        self.orig_label.setText(orig_k)
        self.trans_edit.blockSignals(True)
        self.trans_edit.setText(trans_k)
        self.trans_edit.blockSignals(False)
        self.full_content_display.setPlainText(content_k)
        self.current_orig_key_for_editor = orig_k
        self.current_translation_in_editor_before_change = trans_k
        self.translator_save_status_label.setText("<b>Saved ✅</b>")
        logger.debug(f"Cell clicked R{row}, UID: '{_uid}', Orig: '{orig_k}', Trans: '{trans_k}'.")

    def apply_edited_translation(self):
        self.translator_debounce_timer.stop()
        if self.main_window.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot save edits while translations active.")
            return
        if self.current_row is None or not (0 <= self.current_row < len(self.table_data)):
            logger.warning("Apply edited translation: No row selected or row is out of bounds.")
            return

        row_idx = self.current_row
        uid, orig_k_tbl, _, _ = self.table_data[row_idx]

        if self.current_orig_key_for_editor != orig_k_tbl:
            logger.warning(f"Editor original key '{self.current_orig_key_for_editor}' mismatches table key '{orig_k_tbl}'. Aborting apply.")
            QtWidgets.QMessageBox.warning(self, "Save Error", "Editor state seems to mismatch the selected row. Please re-select the row and try again.")
            return

        new_trans_edit = self.trans_edit.text().strip()
        
        if new_trans_edit == self.current_translation_in_editor_before_change:
            logger.debug("Skipping apply, translation text has not changed.")
            return

        tgt_lang = self.current_target_language
        src_lang = self.current_source_language
        if not tgt_lang:
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Cannot apply translation: No target language is selected.")
            return
        if not src_lang:
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Cannot apply translation: The LORE-book's source language is not set.")
            return

        if self.main_window._update_translation_cache(uid, orig_k_tbl, new_trans_edit, src_lang, tgt_lang):
            self.table_data[row_idx][2] = new_trans_edit
            item = self.table.item(row_idx, 2)
            if item:
                item.setText(new_trans_edit)
            else:
                self.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(new_trans_edit))
            
            self.current_translation_in_editor_before_change = new_trans_edit
            self.translator_save_status_label.setText("<b>Applied ✅</b>")

            self.main_window.set_dirty_flag(True)
            
            self.main_window.status_bar.showMessage(f"Applied edit for '{orig_k_tbl}' (UID {uid}). Saving pending...", 3000)
            logger.info(f"Applied manual translation for '{orig_k_tbl}' (UID {uid}) to '{new_trans_edit}' for {tgt_lang}. Save requested.")
        else:
            self.main_window.status_bar.showMessage(f"Failed to update LORE data for UID {uid}.", 5000)
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Failed to update LORE data for UID {uid}. See logs for details.")

    def delete_selected_translations_action(self):
        if self.main_window.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot delete translations while other operations are active.")
            return

        tgt_lang_to_clear = self.current_target_language
        src_lang_of_lore = self.current_source_language

        if not tgt_lang_to_clear: 
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Cannot delete: No target language selected.")
            return
        if not src_lang_of_lore:
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Cannot delete: LORE-book source language is not set.")
            logger.warning("delete_selected_translations_action: Aborted, missing LORE source language.")
            return

        rows_to_process = []
        selected_indices = self.table.selectionModel().selectedRows()

        if selected_indices:
            rows_to_process = sorted([idx.row() for idx in selected_indices])
            logger.info(f"Attempting to delete translations for {len(rows_to_process)} selected row(s) for language «{tgt_lang_to_clear}».")
        elif self.current_row is not None and (0 <= self.current_row < len(self.table_data)):
            uid_tbl_editor_check, _orig_k_tbl_editor_check, _, _ = self.table_data[self.current_row]
            if self.current_orig_key_for_editor == _orig_k_tbl_editor_check:
                rows_to_process = [self.current_row]
                logger.info(f"Attempting to delete translation for the currently edited row ({self.current_row}) for language «{tgt_lang_to_clear}».")
            else:
                QtWidgets.QMessageBox.warning(self, "Editor Mismatch", "The data in the editor seems out of sync with the table. Please re-select the row.")
                logger.warning("Delete action aborted: Editor data mismatch with table for current_row.")
                return
        else:
            QtWidgets.QMessageBox.information(self, "No Selection", "Please select one or more rows in the table, or ensure a row is active in the editor.")
            return

        if not rows_to_process: 
            logger.warning("delete_selected_translations_action: No rows identified for processing.")
            return

        items_to_confirm_delete = []
        for row_idx in rows_to_process:
            if 0 <= row_idx < len(self.table_data):
                uid, orig_k, trans_val, _ = self.table_data[row_idx]
                if str(trans_val).strip():
                    items_to_confirm_delete.append({'uid': uid, 'orig_k': orig_k, 'trans_val': trans_val, 'row_idx': row_idx})

        if not items_to_confirm_delete: 
            QtWidgets.QMessageBox.information(self, "Nothing to Delete", "No existing translations found for the selected item(s) in the current target language.")
            return

        confirm_message = f"Are you sure you want to delete the following translation(s) for language «{tgt_lang_to_clear}»?\n\n"
        preview_count = 0
        for item_data in items_to_confirm_delete:
            if preview_count < 5:
                confirm_message += f"- UID {item_data['uid']}, Key: '{item_data['orig_k']}' -> '{item_data['trans_val']}'\n"
            preview_count +=1
        if len(items_to_confirm_delete) > 5: 
            confirm_message += f"...and {len(items_to_confirm_delete) - 5} more item(s).\n"
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Delete Translations', confirm_message, QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            deleted_count = 0
            for item_data in items_to_confirm_delete:
                uid = item_data['uid']
                orig_k_tbl = item_data['orig_k']
                row_idx_del = item_data['row_idx']
                if self.main_window._update_translation_cache(uid, orig_k_tbl, "", src_lang_of_lore, tgt_lang_to_clear):
                    self.table_data[row_idx_del][2] = ""
                    table_item_to_update = self.table.item(row_idx_del, 2)
                    if table_item_to_update:
                        table_item_to_update.setText("")
                    else:
                        self.table.setItem(row_idx_del, 2, QtWidgets.QTableWidgetItem(""))
                    if self.current_row == row_idx_del and self.current_orig_key_for_editor == orig_k_tbl:
                        self.trans_edit.clear()
                        self.current_translation_in_editor_before_change = ""
                    deleted_count += 1
                    logger.info(f"Deleted translation from cache for '{orig_k_tbl}' (UID {uid}, lang: {tgt_lang_to_clear}).")
                else: 
                    logger.error(f"Failed to update cache for UID {uid}, Key '{orig_k_tbl}' during delete operation.")
            if deleted_count > 0:
                self.main_window.set_dirty_flag(True)
                self.main_window.status_bar.showMessage(f"Deleted {deleted_count} translation(s) for language '{tgt_lang_to_clear}'.", 5000)
                
            else: 
                self.main_window.status_bar.showMessage("No translations were deleted (operation might have failed internally).", 5000)
        else: 
            logger.info("Deletion of selected translations cancelled by user.")

    def translate_selected_rows_action(self):
        if not self.main_window.data: 
            QtWidgets.QMessageBox.information(self, "Info", "Load or create a LORE-book first.")
            return
        sel_indices = self.table.selectionModel().selectedRows()
        if not sel_indices: 
            QtWidgets.QMessageBox.information(self, "Info", "Select row(s).")
            return
        sel_rows = sorted([idx.row() for idx in sel_indices])
        tgt_lang = self.current_target_language
        src_lang = self.current_source_language
        if not tgt_lang: 
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Select target lang.")
            return
        if not src_lang: 
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Select source lang.")
            return
        jobs = self.main_window._prepare_jobs_for_rows(sel_rows, src_lang, tgt_lang, False)
        if jobs: 
            self.main_window._start_translation_batch(jobs, "Translating Selected")
        else: 
            QtWidgets.QMessageBox.information(self, "Already Translated", "Selected items already translated/cached. Use '«Regenerate».")
            self.main_window.status_bar.showMessage("Selected items already translated/cached.", 3000)
    
    def translate_all_action(self):
        if not self.main_window.data:
            QtWidgets.QMessageBox.information(self, "Info", "Load or create a LORE-book first.")
            return
        all_rows = list(range(len(self.table_data)))
        if not all_rows: 
            QtWidgets.QMessageBox.information(self, "Empty Table", "No data in table.")
            return
        tgt_lang = self.current_target_language
        src_lang = self.current_source_language
        if not tgt_lang: 
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Select target lang.")
            return
        if not src_lang: 
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Select source lang.")
            return
        jobs = self.main_window._prepare_jobs_for_rows(all_rows, src_lang, tgt_lang, False)
        if jobs: 
            self.main_window._start_translation_batch(jobs, "Translating All")
        else: 
            QtWidgets.QMessageBox.information(self, "All Translated", "All items appear translated/cached. Use «Regenerate» or clear cache.")
            self.main_window.status_bar.showMessage("All items already translated/cached.", 3000)

    def regenerate_selected_translation_action(self):
        if not self.main_window.data: 
            QtWidgets.QMessageBox.information(self, "Info", "Load or create a LORE-book first.")
            return
        sel_rows = []
        sel_indices = self.table.selectionModel().selectedRows()
        if sel_indices: 
            sel_rows = sorted([idx.row() for idx in sel_indices])
        elif self.current_row is not None and (0 <= self.current_row < len(self.table_data)):
            sel_rows = [self.current_row]
        if not sel_rows: 
            QtWidgets.QMessageBox.information(self, "Info", "Select row(s) or ensure row active in editor.")
            return
        tgt_lang = self.current_target_language
        src_lang = self.current_source_language
        if not tgt_lang: 
            QtWidgets.QMessageBox.warning(self, "No Target Language", "Select target lang for regen.")
            return
        if not src_lang: 
            QtWidgets.QMessageBox.warning(self, "No Source Language", "Select source lang for regen.")
            return
        jobs = self.main_window._prepare_jobs_for_rows(sel_rows, src_lang, tgt_lang, True)
        if jobs: 
            self.main_window._start_translation_batch(jobs, "Regenerating")
        else: 
            self.main_window.status_bar.showMessage("No items selected/prepared for regen.", 3000)
            logger.warning("Regen req, but no jobs prepped. Rows: %s", sel_rows)

    @QtCore.Slot(str)
    def filter_translation_table(self, search_term):
        if not self.main_window.data: 
            return
        term = search_term.lower()
        for i in range(self.table.rowCount()):
            original_item = self.table.item(i, 1)
            translated_item = self.table.item(i, 2)
            uid_item = self.table.item(i, 0)
            match = False
            if term == "": 
                match = True
            else:
                if uid_item and term in uid_item.text().lower():
                    match = True
                if not match and original_item and term in original_item.text().lower():
                    match = True
                if not match and translated_item and term in translated_item.text().lower(): 
                    match = True
            self.table.setRowHidden(i, not match)

    @QtCore.Slot()
    def force_apply_edit(self):
        if self.translator_debounce_timer.isActive():
            self.translator_debounce_timer.stop()
        self.apply_edited_translation()

    @QtCore.Slot()
    def _trigger_translator_debounce_save(self):
        if self.current_row is not None:
            self.translator_save_status_label.setText("<i>Changes detected...</i>")
            self.translator_debounce_timer.start()

    def _create_debounce_timer(self, slot_function, interval=1000):
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(slot_function)
        return timer

class TranslatorApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f'Lorebook Gemini Translator v{APP_VERSION}')
        self.resize(1100, 850)
        self.cache = {}
        self.cache_file_path = None
        self.data = None
        self.input_path = None
        self.is_dirty = False

        self.recent_files = current_settings.get("recent_files", [])
        self.recent_menu = None
        self.qt_log_handler = None
        self.model_inspector_window = None
        self.thread_pool = QtCore.QThreadPool() 
        logger.debug(f"QThreadPool maxThreadCount: {self.thread_pool.maxThreadCount()}")
        
        self.pending_translation_jobs = collections.deque()
        self.active_translation_jobs = 0
        self.progress_dialog = None
        self.translation_timer = QtCore.QTimer(self)
        self.translation_timer.setSingleShot(True)
        self.translation_timer.timeout.connect(self._dispatch_next_job_to_pool)
        self.total_jobs_for_progress = 0
        self.completed_jobs_for_progress = 0

        self.api_request_timestamps_per_key = {}
        self.api_key_cooldown_end_times = {}
        self.discovered_rpm_limits = {}
        self.rpm_monitor_timer = QtCore.QTimer(self)
        self.rpm_monitor_timer.timeout.connect(self.update_rpm_display_and_check_cooldown)

        self.cache_save_timer = self._create_debounce_timer(self.save_cache, 3000)
        self.auto_save_timer = self._create_debounce_timer(self.save_all_changes, 3000)
        
        self.init_ui()
        
        
        if self.translation_tab and self.translation_tab.get_log_text_edit():
            self.qt_log_handler = QtLogHandler(self.translation_tab.get_log_text_edit())
            logger.addHandler(self.qt_log_handler)
        
        self.apply_settings_effects()
        self.update_recent_files_menu()
        logger.info("Application initialized.")

    def _create_debounce_timer(self, slot_function, interval=1000):
        timer = QtCore.QTimer(self)
        timer.setSingleShot(True)
        timer.setInterval(interval)
        timer.timeout.connect(slot_function)
        return timer

    def request_cache_save(self):
        if self.cache_file_path:
            logger.debug(f"Requesting a debounced cache save to {self.cache_file_path}.")
            self.cache_save_timer.start()

    def init_ui(self):
        self.create_actions()
        self.create_menus()

        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready. Use File -> New or Open to start.")

        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)

        tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(tab_widget)

        self.editor_tab = EditorTab(self)
        self.translation_tab = TranslationTab(self)
        
        self.editor_tab.search_term_changed.connect(self.translation_tab.filter_translation_table)

        generation_tab = QtWidgets.QWidget()
        generation_layout = QtWidgets.QVBoxLayout(generation_tab)
        generation_label = QtWidgets.QLabel("In development")
        generation_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        generation_layout.addWidget(generation_label)

        prompt_editor_tab = QtWidgets.QWidget()
        prompt_editor_layout = QtWidgets.QVBoxLayout(prompt_editor_tab)
        prompt_editor_label = QtWidgets.QLabel("In development")
        prompt_editor_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        prompt_editor_layout.addWidget(prompt_editor_label)
        
        tab_widget.addTab(self.editor_tab, "Editor")
        tab_widget.addTab(generation_tab, "Generation")
        tab_widget.addTab(self.translation_tab, "Translation")
        tab_widget.addTab(prompt_editor_tab, "Promt Editor")

        tab_widget.setCurrentIndex(2)

    def set_dirty_flag(self, dirty=True):
        if dirty and not self.is_dirty:
            self.is_dirty = True
            if not self.windowTitle().endswith('*'):
                self.setWindowTitle(f"{self.windowTitle()}*")
            self.auto_save_timer.start()
        elif not dirty and self.is_dirty:
            self.is_dirty = False
            if self.auto_save_timer.isActive():
                self.auto_save_timer.stop()
            base_title = f'Lorebook Gemini Translator v{APP_VERSION}'
            if self.input_path:
                file_name = os.path.basename(self.input_path)
                self.setWindowTitle(f'{base_title} - {file_name}')
            elif self.data:
                lore_name = self.data.get("name", "New LORE-book")
                self.setWindowTitle(f'{base_title} - {lore_name}')
            else:
                self.setWindowTitle(base_title)

    def _mask_api_key(self, api_key_string: str) -> str:
        if not api_key_string: 
            return "N/A_KEY"
        if len(api_key_string) > 7: 
            return f"{api_key_string[:3]}...{api_key_string[-4:]}"
        elif len(api_key_string) > 0: 
            return "****"
        return "EMPTY_KEY"

    def _get_effective_rpm_limit_for_model(self, model_name: str) -> int:
        if model_name in self.discovered_rpm_limits:
            discovered_limit = self.discovered_rpm_limits[model_name]

            if self.active_translation_jobs > 0 or self.pending_translation_jobs:
                logger.debug(f"Using discovered RPM limit for model '{model_name}': {discovered_limit} (user setting: {current_settings.get('rpm_limit', default_settings['rpm_limit'])})")
            
            return discovered_limit
            
        return current_settings.get("rpm_limit", default_settings["rpm_limit"])

    def find_entry_dict_key_by_uid(self, uid_to_find):
        if self.data and 'entries' in self.data:
            uid_to_find_str = str(uid_to_find)
            for dict_key, entry_data_val in self.data['entries'].items():
                if isinstance(entry_data_val, dict):
                    entry_uid_val = entry_data_val.get('uid')
                    if entry_uid_val is not None and str(entry_uid_val) == uid_to_find_str: 
                        return dict_key
        logger.warning(f"Could not find LORE entry dict key for UID '{uid_to_find}'.")
        return None

    def _ensure_entry_key_is_list(self, entry_data):
            if not isinstance(entry_data, dict): 
                return
            current_primary_key_field = entry_data.get('key')
            consolidated_keys = set()
            if isinstance(current_primary_key_field, str) and current_primary_key_field.strip(): 
                consolidated_keys.add(current_primary_key_field.strip())
            elif isinstance(current_primary_key_field, list):
                for item in current_primary_key_field:
                    if isinstance(item, str) and item.strip(): 
                        consolidated_keys.add(item.strip())
            entry_data['key'] = sorted(list(consolidated_keys))

    @QtCore.Slot(str, str, str, dict)
    def handle_inspector_update(self, prompt, final_translation, thinking_text, usage_metadata):
        if self.model_inspector_window and self.model_inspector_window.isVisible():
            self.model_inspector_window.update_data(prompt, final_translation, thinking_text, usage_metadata)

    def apply_rpm_settings_effects(self):
        update_interval = current_settings.get("rpm_monitor_update_interval_ms", 1000)
        if self.rpm_monitor_timer.isActive():
            self.rpm_monitor_timer.stop()
        self.rpm_monitor_timer.start(update_interval)
        self.update_rpm_display_and_check_cooldown()
        rpm_limit_val = self._get_effective_rpm_limit_for_model(current_settings.get("gemini_model"))
        logger.info(f"RPM (per key) monitor: Effective Limit {rpm_limit_val}, Warn {current_settings.get('rpm_warning_threshold_percent', 75)}%, UI Update {update_interval}ms.")

    def _record_api_request_timestamp(self, api_key_used: str):
        if not api_key_used:
            logger.warning("Attempted to record API timestamp for empty API key.")
            return
        now = time.monotonic()
        if api_key_used not in self.api_request_timestamps_per_key:
            self.api_request_timestamps_per_key[api_key_used] = collections.deque()
        self.api_request_timestamps_per_key[api_key_used].append(now)

    def _get_current_rpm_for_key(self, api_key: str) -> int:
        if not api_key:
            return 0
        now = time.monotonic()
        timestamps_deque = self.api_request_timestamps_per_key.get(api_key)
        if not timestamps_deque: 
            return 0
        while timestamps_deque and timestamps_deque[0] < now - 60: 
            timestamps_deque.popleft()
        return len(timestamps_deque)

    def _is_rpm_limit_reached_for_key(self, api_key: str) -> bool:
        if not api_key:
            return True
        model_being_used = current_settings.get("gemini_model")
        effective_limit = self._get_effective_rpm_limit_for_model(model_being_used)
        return self._get_current_rpm_for_key(api_key) >= effective_limit

    def update_rpm_display_and_check_cooldown(self):
        if not hasattr(self, 'translation_tab') or not hasattr(self.translation_tab, 'rpm_status_label'):
            return

        now = time.monotonic()
        active_api_keys = current_settings.get("api_keys", [])
        current_model_for_rpm_calc = current_settings.get("gemini_model")
        effective_rpm_limit_for_this_model = self._get_effective_rpm_limit_for_model(current_model_for_rpm_calc)

        keys_to_remove_from_cooldown = [k for k, end_time in self.api_key_cooldown_end_times.items() if end_time <= now]
        for key in keys_to_remove_from_cooldown:
            if key in self.api_key_cooldown_end_times:
                del self.api_key_cooldown_end_times[key]
                logger.info(f"API key {self._mask_api_key(key)} exited RPM cooldown.")

        overall_status_lines = []
        text_color_hex = "#00FF00"
        if not active_api_keys:
            overall_status_lines.append("RPM: No API Keys")
            text_color_hex = "#FFA500"
        else:
            total_potential_rpm = 0
            current_total_used_rpm = 0
            available_keys_count = 0
            keys_in_cooldown = 0
            for key in active_api_keys:
                cooldown_end = self.api_key_cooldown_end_times.get(key)
                if cooldown_end and cooldown_end > now:
                    keys_in_cooldown += 1
                    continue
                available_keys_count += 1
                total_potential_rpm += effective_rpm_limit_for_this_model
                current_total_used_rpm += self._get_current_rpm_for_key(key)

            if available_keys_count > 0:
                line1 = f"Total RPM: {current_total_used_rpm}/{total_potential_rpm} (on {available_keys_count} key)"
                overall_status_lines.append(line1)
                if total_potential_rpm > 0:
                    usage = (current_total_used_rpm / total_potential_rpm) * 100
                    warn_thresh = current_settings.get("rpm_warning_threshold_percent", 75)
                    if usage >= 100:
                        text_color_hex = "#FF0000"
                    elif usage >= warn_thresh:
                        text_color_hex = "#FFA500"
                    else:
                        text_color_hex = "#00FF00"
                else:
                    text_color_hex = "#808080"
            elif keys_in_cooldown == len(active_api_keys):
                min_wait = min((self.api_key_cooldown_end_times.get(k, now) - now for k in active_api_keys if self.api_key_cooldown_end_times.get(k,0) > now), default=float('inf'))
                wait_msg = f"{int(min_wait)}s" if min_wait != float('inf') else "..."
                line1 = f"All {keys_in_cooldown} key(s) in cooldown. Min wait: {wait_msg}"
                overall_status_lines.append(line1)
                text_color_hex = "#FF0000"
            else: 
                overall_status_lines.append("RPM: Status Error")
                text_color_hex = "#FF0000"

            num_keys = len(active_api_keys)
            current_rot_idx = current_settings.get("current_api_key_index", 0)
            line2 = "Next Key: N/A"
            if num_keys > 0:
                key_to_disp = active_api_keys[current_rot_idx % num_keys]
                cooldown_end_disp = self.api_key_cooldown_end_times.get(key_to_disp)
                if cooldown_end_disp and cooldown_end_disp > now:
                    line2 = f"Next Key ({self._mask_api_key(key_to_disp)}): Cooldown {int(cooldown_end_disp - now)}s"
                else:
                    key_rpm_disp = self._get_current_rpm_for_key(key_to_disp)
                    limit_hit_disp = " (Limit!)" if self._is_rpm_limit_reached_for_key(key_to_disp) else ""
                    line2 = f"Next Key ({self._mask_api_key(key_to_disp)}): {key_rpm_disp}/{effective_rpm_limit_for_this_model} RPM{limit_hit_disp}"
            overall_status_lines.append(line2)

        self.translation_tab.rpm_status_label.setText("\n".join(overall_status_lines))
        self.translation_tab.rpm_status_label.setStyleSheet(f"QLabel {{ color : {text_color_hex}; font-weight: bold; }}")

        if self.pending_translation_jobs and not self.translation_timer.isActive():
            can_dispatch = False
            active_api_keys = current_settings.get("api_keys", [])
            if active_api_keys:
                now = time.monotonic()
                for key_chk in active_api_keys:
                    cooldown_end_chk = self.api_key_cooldown_end_times.get(key_chk)
                    if not (cooldown_end_chk and cooldown_end_chk > now):
                        if not self._is_rpm_limit_reached_for_key(key_chk):
                            can_dispatch = True
                            break
            if can_dispatch:
                logger.info("RPM monitor detected pending jobs and available keys. Triggering dispatch.")
                self.translation_timer.start(0)

    def create_actions(self):
        self.new_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-new"), "&New LORE-book", self)
        self.new_action.setShortcut(QtGui.QKeySequence.New)
        self.new_action.triggered.connect(self.new_lorebook)
        
        self.open_action=QtGui.QAction(QtGui.QIcon.fromTheme("document-open"),"&Open...",self)
        self.open_action.setShortcut(QtGui.QKeySequence.Open)
        self.open_action.triggered.connect(self.browse_and_load)
        
        self.save_action = QtGui.QAction(QtGui.QIcon.fromTheme("document-save"), "&Save", self)
        self.save_action.setShortcut(QtGui.QKeySequence.Save)
        self.save_action.triggered.connect(self.save_all_changes)
        self.save_action.setEnabled(False)

        self.export_action=QtGui.QAction(QtGui.QIcon.fromTheme("document-send"),"&Export LORE-book...",self)
        self.export_action.setShortcut("Ctrl+E")
        self.export_action.triggered.connect(self.export_lorebook)
        self.export_action.setEnabled(False)

        self.exit_action=QtGui.QAction(QtGui.QIcon.fromTheme("application-exit"),"E&xit",self)
        self.exit_action.setShortcut(QtGui.QKeySequence.Quit)
        self.exit_action.triggered.connect(self.close)
        
        self.settings_action=QtGui.QAction(QtGui.QIcon.fromTheme("preferences-system"),"&Settings...",self)
        self.settings_action.triggered.connect(self.open_settings_dialog)
        
        self.toggleModelInspectorAction=QtGui.QAction("Model Inspector",self,checkable=True)
        self.toggleModelInspectorAction.setStatusTip("Show/Hide model inspector")
        self.toggleModelInspectorAction.triggered.connect(self.toggle_model_inspector)
        
        self.about_action = QtGui.QAction("About", self)
        self.about_action.triggered.connect(self.show_about_dialog)

    def create_menus(self):
        self.file_menu=self.menuBar().addMenu("&File")
        self.file_menu.addAction(self.new_action)
        self.file_menu.addAction(self.open_action)
        self.recent_menu = self.file_menu.addMenu("Open &Recent")
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.save_action)
        self.file_menu.addAction(self.export_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.settings_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.exit_action)
        
        self.view_menu=self.menuBar().addMenu("&View")
        self.view_menu.addAction(self.toggleModelInspectorAction)
        
        self.help_menu = self.menuBar().addMenu("&Help")
        self.help_menu.addAction(self.about_action)

    def show_about_dialog(self):
        dialog = AboutDialog(self)
        dialog.exec()

    def update_recent_files(self, new_path):
        if not new_path:
            return
        if new_path in self.recent_files:
            self.recent_files.remove(new_path)
        self.recent_files.insert(0, new_path)
        self.recent_files = self.recent_files[:MAX_RECENT_FILES]
        current_settings["recent_files"] = self.recent_files

    def update_recent_files_menu(self):
        if not self.recent_menu:
            return
        self.recent_menu.clear()
        self.recent_files = [p for p in current_settings.get("recent_files", []) if p and os.path.exists(p)]
        current_settings["recent_files"] = self.recent_files
        if not self.recent_files: 
            self.recent_menu.setEnabled(False)
            return
        self.recent_menu.setEnabled(True)
        for i, path in enumerate(self.recent_files):
            action = QtGui.QAction(f"&{i+1}. {os.path.basename(path)}", self)
            action.setData(path)
            action.triggered.connect(self.load_file_from_history_action)
            self.recent_menu.addAction(action)
        self.recent_menu.addSeparator()
        clear_action = QtGui.QAction("Clear Recent Files List", self)
        clear_action.triggered.connect(self.clear_recent_files_list_action)
        self.recent_menu.addAction(clear_action)

    def load_file_from_history_action(self):
        action = self.sender()
        if action and isinstance(action, QtGui.QAction):
            path = action.data()
            if path and os.path.exists(path):
                if self.active_translation_jobs > 0:
                    QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot load new file while translations active.")
                    return
                self.load_file(path)
            elif path:
                QtWidgets.QMessageBox.warning(self, "File Not Found", f"File '{path}' no longer exists.")
                if path in current_settings["recent_files"]:
                    current_settings["recent_files"].remove(path)
                    save_settings()
                    self.update_recent_files_menu()

    def clear_recent_files_list_action(self):
        reply = QtWidgets.QMessageBox.question(self, "Clear Recent Files", "Clear list of recent files?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.recent_files.clear()
            current_settings["recent_files"] = []
            save_settings()
            self.update_recent_files_menu()
            logger.info("Recent files list cleared.")
            
    def toggle_model_inspector(self):
        if not self.model_inspector_window:
            self.model_inspector_window = ModelInspectorDialog(self)
        if self.model_inspector_window.isVisible():
            self.model_inspector_window.hide()
            self.toggleModelInspectorAction.setChecked(False)
            logger.debug("Inspector hidden.")
        else:
            self.model_inspector_window.show()
            self.model_inspector_window.raise_()
            self.model_inspector_window.activateWindow()
            self.toggleModelInspectorAction.setChecked(True)
            logger.debug("Inspector shown.")


    def open_settings_dialog(self):
            global current_settings
            dialog = SettingsDialog(current_settings, self)
            dialog.clear_cache_requested.connect(self.handle_clear_cache_request)
            if dialog.exec() == QtWidgets.QDialog.Accepted:
                new_s_data = dialog.get_settings()

                api_keys_changed = current_settings.get("api_keys", []) != new_s_data.get("api_keys", [])
                model_changed = current_settings.get("gemini_model") != new_s_data.get("gemini_model")
                rpm_limit_changed = current_settings.get("rpm_limit") != new_s_data.get("rpm_limit")

                if api_keys_changed:
                    old_keys = set(current_settings.get("api_keys", []))
                    new_keys_set = set(new_s_data.get("api_keys", []))
                    removed_keys = old_keys - new_keys_set
                    for r_key in removed_keys:
                        if r_key in self.api_request_timestamps_per_key:
                            del self.api_request_timestamps_per_key[r_key]
                        if r_key in self.api_key_cooldown_end_times:
                            del self.api_key_cooldown_end_times[r_key]

                if model_changed or rpm_limit_changed:
                    self.discovered_rpm_limits.clear()
                    logger.info("All dynamically discovered RPM limits have been reset due to settings change.")

                current_settings.update(new_s_data)
                if model_changed:
                    self.translation_tab.update_model_specific_ui()
                save_settings()

                self.apply_settings_effects() 
                logger.info("Settings updated and effects applied.")

                if (api_keys_changed or model_changed) and current_settings.get("api_keys"):
                    logger.info("Validating new API/model settings...")
                    try:
                        test_k = current_settings["api_keys"][0]
                        test_m = current_settings.get("gemini_model")
                        masked_k_log = self._mask_api_key(test_k)
                        logger.info(f"Attempting to validate with key {masked_k_log} and model {test_m}")
                        client = genai.Client(api_key=test_k)
                        models = client.models.list()
                        model_found = any(test_m in m.name for m in models)
                        
                        if not model_found:
                            raise ValueError(f"Model '{test_m}' not found or not available with this API key.")

                        logger.info(f"API Client and model '{test_m}' validated successfully.")
                        QtWidgets.QMessageBox.information(self, "Settings Validated", f"Successfully connected to the API with the new settings and model '{test_m}'.")
                    except Exception as e:
                        logger.error(f"Failed to validate new API key/model settings: {e}", exc_info=True)
                        QtWidgets.QMessageBox.warning(self, "Settings Validation Failed", f"Could not validate the new API or model settings:\n\n{e}\n\nTranslations may fail.")

    def handle_clear_cache_request(self):
        if not self.cache_file_path:
            QtWidgets.QMessageBox.information(self, "Info", "No LORE-book loaded, no cache to clear.")
            logger.info("Clear cache: No active lorebook cache.")
            return
        reply = QtWidgets.QMessageBox.question(self, 'Confirm Cache Clear', f"Clear translation cache for current file?\n({os.path.basename(self.cache_file_path)})", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            self.cache.clear()
            cache_file_deleted = False
            if os.path.exists(self.cache_file_path):
                try:
                    os.remove(self.cache_file_path)
                    logger.info(f"Cache file {self.cache_file_path} deleted.")
                    cache_file_deleted = True
                except Exception as e:
                    logger.error(f"Failed to delete cache file {self.cache_file_path}: {e}")
                    QtWidgets.QMessageBox.warning(self, "Cache Clear Error", f"Could not delete cache file: {e}")
            else:
                logger.info(f"Cache file {self.cache_file_path} not found (already cleared).")
            msg = f"Cache file {os.path.basename(self.cache_file_path)} and in-memory cache cleared." if cache_file_deleted else "In-memory cache cleared. Cache file not found/deleted."
            QtWidgets.QMessageBox.information(self, "Cache Cleared", msg)
            if self.data:
                self.translation_tab.populate_table_data()
            self.status_bar.showMessage(f"Cache for {os.path.basename(self.input_path)} cleared.")

    def apply_settings_effects(self): 
        setup_logger()
        self.apply_rpm_settings_effects()
        if hasattr(self, 'translation_tab'):
            self.translation_tab.set_log_panel_visibility(current_settings.get("show_log_panel", True))
        logger.info("Settings effects applied.")

    def browse_and_load(self):
        if self.active_translation_jobs > 0:
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot load new file while translations active.")
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Open LORE-book', os.path.expanduser("~"), 'LORE-book (*.json);;All Files (*)')
        if path:
            self.load_file(path)

    @QtCore.Slot()
    def new_lorebook(self):
        if self.is_dirty:
            reply = QtWidgets.QMessageBox.question(self, "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them and create a new LORE-book?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                QtWidgets.QMessageBox.No)
            if reply == QtWidgets.QMessageBox.No:
                return

        output_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Create New LORE-book", os.path.expanduser("~"), "LORE-book (*.json);;All Files (*)")

        if not output_path:
            logger.info("New LORE-book creation cancelled by user.")
            return

        logger.info(f"Creating and saving new LORE-book to {output_path}")

        if self.cache_file_path and self.cache:
            self.save_cache()

        new_data = copy.deepcopy(LOREBOOK_TEMPLATE)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, ensure_ascii=False, indent=2)

            self.load_file(output_path)
            self.set_dirty_flag(False)
            self.status_bar.showMessage(f"Successfully created and loaded '{os.path.basename(output_path)}'.")
            self.save_action.setEnabled(True)

        except Exception as e:
            logger.error(f"Failed to save new LORE-book to {output_path}: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Creation Error", f"Failed to create LORE-book file: {e}")

    def load_file(self, path):
                if not path or not os.path.exists(path):
                    QtWidgets.QMessageBox.critical(self, 'Error', f'File not found: {path}')
                    logger.error(f'LORE-book not found: {path}')
                    return
                if self.is_dirty:
                    self.save_all_changes()

                if self.cache_file_path and self.cache:
                    self.save_cache()

                self._cancel_batch_translation(silent=True)

                self.data = None
                self.cache = {}
                self.cache_file_path = None
                self.input_path = None
                self.editor_tab.editor_clear_form()
                self.editor_tab.editor_set_panel_enabled(False)
                self.editor_tab.editor_refresh_listbox()
                self.translation_tab.table_data = []
                self.translation_tab.update_table_widget()
                logger.info("Application state has been reset before loading new file.")
                
                self.status_bar.showMessage(f"Loading {os.path.basename(path)}...")
                QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
                
                try:
                    with open(path, 'r', encoding='utf-8') as f: 
                        loaded_json = json.load(f)

                    if "entries" not in loaded_json or not isinstance(loaded_json['entries'], dict):
                        raise ValueError("Invalid LORE-book format: Missing 'entries' dictionary.")

                    self.data = loaded_json
                    self.input_path = path

                    self.cache = {}
                    base_name, _ = os.path.splitext(os.path.basename(self.input_path))
                    self.cache_file_path = os.path.join(os.path.dirname(self.input_path), f"{base_name}_translation_cache.json")
                    
                    logger.info(f"Active LORE-book: {self.input_path}")
                    logger.info(f"Project cache path set to: {self.cache_file_path}")

                    self.load_cache()

                    if 'entries' in self.data:
                        for entry_data in self.data['entries'].values():
                            self._ensure_entry_key_is_list(entry_data)
                    
                    logger.info(f"Loaded LORE-book. Entries: {len(self.data.get('entries', {}))}")
                    self.save_action.setEnabled(True)
                    self.export_action.setEnabled(bool(self.data))
                    self.update_recent_files(self.input_path)
                    self.update_recent_files_menu()
                    save_settings()
                
                except Exception as e:
                    QtWidgets.QMessageBox.critical(self, 'LORE-book Load Error', f'Failed to load file: {e}')
                    logger.error(f'LORE-book load error {path}: {e}', exc_info=True)
                    self.data = None
                    self.input_path = None
                    self.cache_file_path = None
                    self.cache = {}
                    self.save_action.setEnabled(False)
                    self.export_action.setEnabled(False)
                    self.editor_tab.on_file_loaded()
                    self.translation_tab.on_file_loaded()
                    self.status_bar.showMessage("Error loading LORE-book.")
                    return
                finally:
                    QtWidgets.QApplication.restoreOverrideCursor()

                self.editor_tab.on_file_loaded()
                self.translation_tab.on_file_loaded()
                
                base_name = os.path.basename(path)
                self.setWindowTitle(f'Lorebook Gemini Translator v{APP_VERSION} - {base_name}')
                self.status_bar.showMessage(f"Loaded {base_name}. {len(self.translation_tab.table_data)} displayable keys.")
                self.translation_tab.update_model_specific_ui()
                self.set_dirty_flag(False)

    def load_cache(self):
        self.cache = {}
        if not self.cache_file_path:
            logger.info("Cache file path not set (new LORE-book). Using in-memory cache.")
            return
        if os.path.exists(self.cache_file_path):
            logger.info(f"Loading cache from: {self.cache_file_path}")
            try:
                with open(self.cache_file_path, 'r', encoding='utf-8') as f:
                    loaded_cache = json.load(f)
                if isinstance(loaded_cache, dict):
                    self.cache = loaded_cache
                    logger.info(f"Loaded cache ({len(self.cache)} entries)")
                else:
                    logger.error(f"Cache file '{self.cache_file_path}' not a JSON dict. Using empty cache.")
            except Exception as e:
                logger.error(f"Error loading cache '{self.cache_file_path}': {e}. Using empty cache.", exc_info=True)
        else:
            logger.info(f"No cache file at '{self.cache_file_path}'. Starting with empty cache for this project.")

    def _generate_cache_key(self, uid, text, src_lang, tgt_lang):
        return f"{str(uid).strip()}_{str(src_lang).strip()}_{str(tgt_lang).strip()}_{hashlib.sha256(str(text).strip().encode('utf-8')).hexdigest()[:16]}"

    def _update_translation_cache(self, uid, orig_key, new_trans, src_lang, tgt_lang):
        if not all([uid, orig_key, tgt_lang, src_lang]):
            logger.warning(f"Cache not updated for UID '{uid}', Orig '{orig_key}': missing IDs.")
            return False
        cache_key = self._generate_cache_key(uid, orig_key, src_lang, tgt_lang)
        new_trans_norm = str(new_trans).strip() if new_trans is not None else None
        if new_trans_norm:
            self.cache[cache_key] = new_trans_norm
            logger.debug(f"Cache memory updated: K='{cache_key}'")
        elif cache_key in self.cache:
            del self.cache[cache_key]
            logger.debug(f"Cache memory cleared: K='{cache_key}'")
        return True
    
    def save_cache(self):
        if not self.cache_file_path: 
            logger.debug("Cache file path not set (new LORE-book). Skipping cache save to disk.")
            return
        logger.info(f"Attempting to save cache to: {self.cache_file_path}. Current in-memory cache size: {len(self.cache)} entries.")
        try:
            temp_path = self.cache_file_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, self.cache_file_path)
            logger.info(f"Cache successfully saved to: {self.cache_file_path}")
        except Exception as e:
            logger.error(f"Cache Save Error to {self.cache_file_path}: {e}", exc_info=True)
            QtWidgets.QMessageBox.warning(self, "Cache Save Error", f"Could not save translation cache to file:\n{self.cache_file_path}\n\nError: {e}")

    def _execute_gemini_api_call_internal(self, client, model_name, text_to_translate, source_lang_name_for_prompt, target_lang_name_for_prompt, context_content_for_api_call):
            prompt_for_inspector = "Error: Prompt not captured."
            thinking_text_output = ""
            final_processed_translation = ""
            usage_metadata_output = {}

            base_prompt_template = (
                "You are a master linguist and loremaster specializing in video game localization. "
                "Your task is to translate LORE keywords from {source_language_name} into {target_language_name}.\n\n"
                "Instructions:\n"
                "The translation MUST be concise, accurate, and function effectively as a search key or in-game display term.\n"
                "For proper nouns (character names, specific unique locations, named items/technologies):\n"
                "    *   Prioritize officially localized terms or widely accepted community translations for {target_language_name} if they exist for the specific game world this LORE belongs to.\n"
                "    *   If no established translation exists, provide a phonetically accurate and natural-sounding transliteration.\n"
                "    *   If the term is a common {source_language_name} word used as a name (e.g., 'The Afterlife' club in English), translate it if a direct, natural, and fitting equivalent exists in {target_language_name}; otherwise, transliterate or use the original {source_language_name} if that's common practice.\n"
                "{context_instructions}\n\n"
                "Your SOLE output MUST be the translated keyword/phrase. Do NOT include any surrounding text, explanations, or quotation marks. Provide ONLY the final translation.\n\n"
                "Now, process the following:"
                "{source_language_name} keyword:  \"{keyword}\"\n"
                "{target_language_name} translation:")
            
            context_instr = ""
            context_section_text = "No additional context provided for this API call."
            
            enable_thinking = current_settings.get("enable_model_thinking", True)
            thinking_budget_from_settings = current_settings.get("thinking_budget_value", -1)

            if context_content_for_api_call and str(context_content_for_api_call).strip():
                context_instr = "The provided context (inside <context> tags) is CRUCIAL. Analyze it carefully to understand the keyword's meaning, usage, and significance within the LORE. This will help you decide between translation, transliteration, or neologism.\n\n<context>\n{context_section}\n</context>"
                context_section_text = str(context_content_for_api_call).strip()
            
            try:
                fmt_ctx_instr = context_instr.format(context_section=context_section_text) if "{context_section}" in context_instr else context_instr
                prompt_for_inspector = base_prompt_template.format(
                    source_language_name=source_lang_name_for_prompt, 
                    target_language_name=target_lang_name_for_prompt, 
                    keyword=text_to_translate, 
                    context_instructions=fmt_ctx_instr
                )
            except KeyError as e_f:
                logger.error(f"Prompt format error (KeyError: '{e_f}'). This should not happen.")
                return prompt_for_inspector, "", "", "Prompt format error", {}

            log_thinking_status = "OFF"
            if enable_thinking:
                log_thinking_status = f"ON (Budget: {'Dynamic' if thinking_budget_from_settings == -1 else thinking_budget_from_settings})"
            
            logger.info(f"API Call: Translating '{text_to_translate}' from '{source_lang_name_for_prompt}' to '{target_lang_name_for_prompt}' (thinking: {log_thinking_status}, ctx: {bool(context_content_for_api_call and str(context_content_for_api_call).strip())})")

            try:
                if not client:
                    raise ValueError("Client object not provided to API call function.")

                thinking_config = None

                if enable_thinking:
                    thinking_config = types.ThinkingConfig(
                        include_thoughts=True,
                        thinking_budget=thinking_budget_from_settings
                    )

                elif "flash" in model_name.lower():
                    thinking_config = types.ThinkingConfig(thinking_budget=0)

                config = types.GenerateContentConfig(
                    thinking_config=thinking_config,
                    safety_settings=[
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                        types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                    ]
                )
                
                response = client.models.generate_content(
                    model=f"models/{model_name}", 
                    contents=prompt_for_inspector, 
                    config=config
                )

                raw_resp_text_parts = []
                thinking_text_parts = []
                
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        part_text = getattr(part, 'text', '')
                        if not part_text: 
                            continue
                        if hasattr(part, 'thought') and part.thought:
                            thinking_text_parts.append(part_text)
                        else:
                            raw_resp_text_parts.append(part_text)

                thinking_text_output = "".join(thinking_text_parts)
                final_processed_translation = "".join(raw_resp_text_parts).strip()

                if hasattr(response, 'usage_metadata'):
                    usage_metadata_output['prompt'] = getattr(response.usage_metadata, 'prompt_token_count', 'N/A')
                    if hasattr(response.usage_metadata, 'thoughts_token_count'):
                        usage_metadata_output['thoughts'] = getattr(response.usage_metadata, 'thoughts_token_count', 'N/A')
                    usage_metadata_output['candidates'] = getattr(response.usage_metadata, 'candidates_token_count', 'N/A')
                    usage_metadata_output['total'] = getattr(response.usage_metadata, 'total_token_count', 'N/A')

                logger.info(f"API Call Result for '{text_to_translate}' -> '{final_processed_translation}'")

            except (ResourceExhausted, errors.ClientError) as e_quota:
                raise e_quota

            except Exception as e_api:
                error_type = type(e_api).__name__
                logger.error(f"Gemini API call failed for '{text_to_translate}': {error_type} - {e_api}", exc_info=True)
                error_message = f"Exception during API call: {error_type} - {e_api}"
                return prompt_for_inspector, "", "", error_message, {}
            return prompt_for_inspector, final_processed_translation, thinking_text_output, usage_metadata_output

    def _get_translation_from_cache_or_prepare_job(self, orig_text, src_lang, tgt_lang, uid, context, force_regen=False, prepare_only=False):
        cache_key = self._generate_cache_key(uid, orig_text, src_lang, tgt_lang)

        if cache_key in self.cache and not force_regen: 
            return self.cache[cache_key], True
        if prepare_only: 
            return None, False
        api_ctx = str(context).strip() if current_settings.get("use_content_as_context", True) and context and str(context).strip() else None
        return {'text_to_translate': orig_text, 'source_lang': src_lang, 'target_lang': tgt_lang, 'uid_val_for_lookup': str(uid),'context_content_for_api': api_ctx}, False

    def _start_translation_batch(self, jobs_to_queue, op_name="Translating"):
        if not current_settings.get("api_keys"): 
            QtWidgets.QMessageBox.critical(self, "API Key Error", "No API keys. Add in Settings.")
            logger.error("Batch start: No API keys.")
            return
        if self.active_translation_jobs > 0: 
            QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Another batch running.")
            return
        if not jobs_to_queue: 
            QtWidgets.QMessageBox.information(self, "No Work", f"No items for {op_name.lower()}.")
            return
        tgt_lang = self.translation_tab.current_target_language
        if not tgt_lang: 
            QtWidgets.QMessageBox.warning(self, "No Target Language", f"Cannot start {op_name.lower()}: No target lang.")
            return
        self.pending_translation_jobs.clear()
        if isinstance(jobs_to_queue, list) and all(isinstance(j, dict) for j in jobs_to_queue):
            self.pending_translation_jobs.extend(jobs_to_queue)
        else:
            logger.error(f"Invalid jobs_to_queue for {op_name}: {type(jobs_to_queue)}.")
            QtWidgets.QMessageBox.critical(self, "Internal Error", "Invalid job data for batch.")
            return
        self.total_jobs_for_progress = len(self.pending_translation_jobs)
        self.completed_jobs_for_progress = 0
        if self.progress_dialog:
            self.progress_dialog.cancel()
            self.progress_dialog.deleteLater()
            self.progress_dialog = None
        self.progress_dialog = QtWidgets.QProgressDialog(f"{op_name} {self.total_jobs_for_progress} item(s) for '{tgt_lang}'", "Cancel", 0, self.total_jobs_for_progress, self)
        self.progress_dialog.setWindowTitle(f"{op_name} Progress")
        flags = self.progress_dialog.windowFlags() & ~QtCore.Qt.WindowContextHelpButtonHint
        self.progress_dialog.setWindowFlags(flags)
        self.progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
        self.progress_dialog.canceled.connect(self._cancel_batch_translation)
        self.progress_dialog.setValue(0)
        self.progress_dialog.setAutoClose(False)
        self.progress_dialog.setAutoReset(False)
        self.progress_dialog.show()
        logger.info(f"Starting batch: {op_name}, {self.total_jobs_for_progress} items for lang '{tgt_lang}'.")
        self.status_bar.showMessage(f"{op_name} {self.total_jobs_for_progress} items for '{tgt_lang}'...")
        if self.total_jobs_for_progress > 0:
            self.translation_timer.start(0)


    def _dispatch_next_job_to_pool(self):
        if not self.pending_translation_jobs:
            logger.debug("Dispatch timer fired, but no more pending jobs.")
            return

        if self.progress_dialog and self.progress_dialog.wasCanceled():
            logger.warning("Dispatch interrupted, progress dialog was cancelled.")
            return

        api_keys = current_settings.get("api_keys", [])
        if not api_keys:
            logger.error("No API keys. Cannot dispatch.")
            if self.progress_dialog: 
                self.progress_dialog.setLabelText("Error: No API keys.")
            self._finalize_batch_translation("failed (no API keys)")
            QtWidgets.QMessageBox.critical(self, "API Key Error", "No API keys. Add in Settings.")
            return

        now = time.monotonic()
        key_to_use = None
        sel_key_orig_idx = -1
        num_k = len(api_keys)
        start_idx_rot = current_settings.get("current_api_key_index", 0)

        for i in range(num_k):
            key_idx_chk = (start_idx_rot + i) % num_k
            cand_key = api_keys[key_idx_chk]
            cooldown_end = self.api_key_cooldown_end_times.get(cand_key)
            if cooldown_end and cooldown_end > now:
                continue
            if self._is_rpm_limit_reached_for_key(cand_key):
                self.api_key_cooldown_end_times[cand_key] = now + RPM_COOLDOWN_SECONDS
                continue

            key_to_use = cand_key
            sel_key_orig_idx = key_idx_chk
            break

        if key_to_use:
            current_settings["current_api_key_index"] = (sel_key_orig_idx + 1) % num_k
            job_data = self.pending_translation_jobs.popleft()
            job_data['api_key'] = key_to_use
            job_data['model_name'] = current_settings.get("gemini_model")
            self._record_api_request_timestamp(key_to_use)
            
            signals = JobSignals()
            signals.job_completed.connect(self._handle_job_completed)
            signals.job_failed.connect(self._handle_job_failed)
            signals.inspector_update.connect(self.handle_inspector_update)

            if self.active_translation_jobs > 0:
                logger.debug(f"PARALLEL DISPATCH: Sending new job while {self.active_translation_jobs} job(s) are still in-flight.")
            
            runnable = TranslationJobRunnable(self, job_data, signals)
            self.thread_pool.start(runnable)
            self.active_translation_jobs += 1
            logger.debug(f"Dispatched job for '{job_data['text_to_translate']}'. In-flight jobs: {self.active_translation_jobs}, Pending queue: {len(self.pending_translation_jobs)}.")
        else:
            logger.warning("No available API key found (all either at RPM limit or in cooldown).")

        if self.pending_translation_jobs:
            final_delay_ms = 0
            if current_settings.get("manual_rpm_control", False):
                base_delay_ms = int(current_settings.get("api_request_delay", 6.0) * 1000)
                final_delay_ms = max(base_delay_ms, 50)
            else:
                effective_rpm = self._get_effective_rpm_limit_for_model(current_settings.get("gemini_model"))
                base_delay_s = 60.0 / effective_rpm if effective_rpm > 0 else 10.0
                final_delay_ms = int(base_delay_s * 1000)

            final_delay_ms += random.randint(50, 250)
            
            logger.info(f"Scheduling next dispatch check in {final_delay_ms / 1000:.2f}s.")
            self.translation_timer.start(final_delay_ms)

    def _handle_job_completed(self, job_data, translated_text):
        self.active_translation_jobs -= 1
        uid = job_data.get('uid_val_for_lookup', 'N/A')
        used_key = job_data.get('api_key', 'UNKNOWN_KEY')
        logger.info(f"Job completed for '{job_data.get('text_to_translate')}' (UID {uid}, Key {self._mask_api_key(used_key)}) -> '{translated_text}'. In-flight jobs remaining: {self.active_translation_jobs}")
        
        row_idx = job_data.get('row_idx', -1)
        orig_key = job_data.get('text_to_translate')
        tgt_lang = job_data.get('target_lang', '')
        src_lang = job_data.get('source_lang')
        
        if all([uid, orig_key, tgt_lang, src_lang]):
            if self._update_translation_cache(uid, orig_key, translated_text, src_lang, tgt_lang):
                self.set_dirty_flag(True)
                
                if tgt_lang == self.translation_tab.current_target_language and 0 <= row_idx < len(self.translation_tab.table_data):
                    tbl_uid, tbl_orig, _, _ = self.translation_tab.table_data[row_idx]
                    if str(tbl_uid) == str(uid) and tbl_orig == orig_key:
                        self.translation_tab.table_data[row_idx][2] = translated_text
                        item = self.translation_tab.table.item(row_idx, 2)
                        if item:
                            item.setText(translated_text)
                        else: 
                            self.translation_tab.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(translated_text))
                        if self.translation_tab.current_row == row_idx and self.translation_tab.current_orig_key_for_editor == orig_key:
                            self.translation_tab.trans_edit.blockSignals(True)
                            self.translation_tab.trans_edit.setText(translated_text)
                            self.translation_tab.trans_edit.blockSignals(False)
                            self.translation_tab.current_translation_in_editor_before_change = translated_text
                            self.translation_tab.translator_save_status_label.setText("<b>Saved ✅</b>")
        else:
            logger.error(f"Missing job_data in _handle_job_completed. UID:{uid},Orig:{orig_key},Tgt:{tgt_lang},Src:{src_lang}. Job:{job_data}")
        
        self._update_progress_dialog()

        if not self.pending_translation_jobs and self.active_translation_jobs == 0:
            self._finalize_batch_translation("completed (last active job finished)")


    def _handle_job_failed(self, job_data, _error_str, _thinking_text, _full_error_details_str, exception_obj, extra_error_details):
            if extra_error_details is None:
                extra_error_details = {}
            
            self.active_translation_jobs -= 1
            uid = job_data.get('uid_val_for_lookup', 'N/A')
            used_key = job_data.get('api_key', 'UNKNOWN_KEY')
            logger.info(f"Handling failed job for '{job_data.get('text_to_translate','Unknown')}' (UID: {uid}). In-flight jobs remaining:: {self.active_translation_jobs}")
            
            is_quota_error = isinstance(exception_obj, (ResourceExhausted, errors.ClientError)) and used_key != 'UNKNOWN_KEY' and ("429" in str(exception_obj) or "RESOURCE_EXHAUSTED" in str(exception_obj).upper())
            
            if is_quota_error:
                logger.warning(f"Quota error for key {self._mask_api_key(used_key)}. Re-queuing job for '{job_data.get('text_to_translate')}'.")
                self.pending_translation_jobs.appendleft(job_data)
                self.completed_jobs_for_progress -= 1

                retry_delay_seconds = extra_error_details.get('retry_delay_seconds')
                cooldown_duration_seconds = RPM_COOLDOWN_SECONDS
                
                if retry_delay_seconds is not None and retry_delay_seconds > 0:
                    cooldown_duration_seconds = retry_delay_seconds + 3
                    logger.info(f"API suggested retry_delay. Cooldown set to {cooldown_duration_seconds}s.")
                else: 
                    logger.info(f"No API retry_delay found. Using default cooldown {cooldown_duration_seconds}s.")
                
                self.api_key_cooldown_end_times[used_key] = time.monotonic() + cooldown_duration_seconds

                current_model = current_settings.get("gemini_model")
                quota_value_from_error = extra_error_details.get('quota_value_from_error')
                
                if quota_value_from_error is not None:
                    discovered_limit_rpm = max(1, int(quota_value_from_error) - 1) 
                    current_effective_limit = self._get_effective_rpm_limit_for_model(current_model)
                    
                    if discovered_limit_rpm < current_effective_limit:
                        self.discovered_rpm_limits[current_model] = discovered_limit_rpm
                        logger.warning(f"Dynamically adjusted effective RPM for model '{current_model}' to {discovered_limit_rpm} (was {current_effective_limit}).")
                        self.status_bar.showMessage(f"Adjusted RPM for {current_model} to {discovered_limit_rpm} (API limit).", 7000)
                
                self.update_rpm_display_and_check_cooldown()

            self._update_progress_dialog()

            if not self.pending_translation_jobs and self.active_translation_jobs == 0:
                self._finalize_batch_translation("completed (last active job failed)")

    def _update_progress_dialog(self):
        self.completed_jobs_for_progress += 1
        if self.progress_dialog:
            if self.progress_dialog.wasCanceled():
                logger.debug("Progress update skipped, dialog cancelled.")
                return
            self.progress_dialog.setValue(self.completed_jobs_for_progress)
            if self.completed_jobs_for_progress >= self.total_jobs_for_progress and self.active_translation_jobs == 0:
                self._finalize_batch_translation("completed normally (all jobs processed)")

    def _finalize_batch_translation(self, reason=""):
        if not self.progress_dialog and self.total_jobs_for_progress == 0 and self.active_translation_jobs == 0:
            return
        logger.info(f"Finalizing batch. Reason: {reason}. Total:{self.total_jobs_for_progress},Done:{self.completed_jobs_for_progress},Active:{self.active_translation_jobs}")
        if self.progress_dialog:
            self.progress_dialog.setValue(self.total_jobs_for_progress)
            self.progress_dialog.done(QtWidgets.QDialog.Accepted)
            self.progress_dialog.deleteLater()
            self.progress_dialog = None

        self.save_cache()

        status_msg = f"Batch {reason}. Processed {self.completed_jobs_for_progress}/{self.total_jobs_for_progress}."
        if "cancel" in reason and self.pending_translation_jobs:
            rem_pend = len(self.pending_translation_jobs)
            if rem_pend > 0:
                status_msg += f" {rem_pend} pending cancelled."
            self.pending_translation_jobs.clear()
        self.status_bar.showMessage(status_msg, 7000)
        logger.info(status_msg)
        self.active_translation_jobs = 0
        self.total_jobs_for_progress = 0
        self.completed_jobs_for_progress = 0

    @QtCore.Slot()
    def _cancel_batch_translation(self, silent=False):
        if not silent:
            logger.warning("Batch translation cancellation requested.")
        self.pending_translation_jobs.clear()
        if self.progress_dialog: 
            self.progress_dialog.setLabelText("Cancelling... Waiting for active jobs.")
        if self.active_translation_jobs == 0: 
            self._finalize_batch_translation("cancelled (no active jobs)")
        else: 
            logger.info(f"Cancel req. {self.active_translation_jobs} job(s) active. Will finalize after last.")

    def _prepare_jobs_for_rows(self, row_indices, src_lang, tgt_lang, force_regen=False):
        jobs = []
        if not tgt_lang: 
            logger.error("Cannot prep jobs: Target lang not set.") 
            QtWidgets.QMessageBox.warning(self, "Target Lang Error", "Target lang not set.")
            return jobs
        if not src_lang: 
            logger.error("Cannot prep jobs: Source lang not set.")
            QtWidgets.QMessageBox.warning(self, "Source Lang Error", "LORE source lang not set.")
            return jobs
        logger.info(f"Prepping jobs for {len(row_indices)} row(s). Src:'{src_lang}',Tgt:'{tgt_lang}',Regen:{force_regen}")
        for row_idx in row_indices:
            if not (0 <= row_idx < len(self.translation_tab.table_data)): 
                logger.warning(f"Skipping row idx {row_idx} for job prep - out of bounds.")
                continue
            uid, orig_k, trans_cell, content = self.translation_tab.table_data[row_idx]
            job_data, is_cached = self._get_translation_from_cache_or_prepare_job(orig_k, src_lang, tgt_lang, uid, content, force_regen, False)
            if is_cached:
                cached_str = str(job_data).strip()
                cell_str = str(trans_cell).strip()
                if cached_str != cell_str:
                    logger.debug(f"Row {row_idx} (UID '{uid}', Orig '{orig_k}'): Update table from cache. Was:'{cell_str}', Is:'{cached_str}'.")
                    self.translation_tab.table_data[row_idx][2] = cached_str
                    item = self.translation_tab.table.item(row_idx, 2)
                    if item: 
                        item.setText(cached_str)
                    else: 
                        self.translation_tab.table.setItem(row_idx, 2, QtWidgets.QTableWidgetItem(cached_str))
                    if self.translation_tab.current_row == row_idx and self.translation_tab.current_orig_key_for_editor == orig_k: 
                        self.translation_tab.trans_edit.setText(cached_str) 
                        self.translation_tab.current_translation_in_editor_before_change = cached_str
                logger.debug(f"Row {row_idx} (UID '{uid}', Orig '{orig_k}'): Trans '{cached_str}' from cache.")
                continue
            if isinstance(job_data, dict):
                job_data['row_idx'] = row_idx
                if not all(k in job_data for k in ['text_to_translate', 'source_lang', 'target_lang', 'uid_val_for_lookup']): 
                    logger.error(f"Internal Error: Job data missing keys for row {row_idx}. Job: {job_data}")
                    continue
                jobs.append(job_data)
                logger.debug(f"Row {row_idx} (UID '{uid}', Orig '{orig_k}'): Job prepped for API to '{tgt_lang}'.")
            else: 
                logger.error(f"Internal Error: _get_translation_from_cache_or_prepare_job unexpected data row {row_idx}. Data: {job_data}")
        if jobs: 
            logger.info(f"Prepared {len(jobs)} job(s) for translation.")
        else: 
            logger.info("No new jobs prepared (all cached or errors).")
        return jobs

    def _check_if_translations_exist(self):
        if not self.data or not self.cache:
            return False
        
        entry_uids = {str(entry.get('uid')) for entry in self.data.get('entries', {}).values() if entry.get('uid') is not None}
        if not entry_uids:
            return False

        for cache_key in self.cache.keys():
            uid_from_key = cache_key.split('_')[0]
            if uid_from_key in entry_uids:
                logger.info(f"Found translation in cache for UID {uid_from_key}. Triggering advanced save dialog.")
                return True
        return False

    def export_lorebook(self):
            if self.active_translation_jobs > 0:
                QtWidgets.QMessageBox.warning(self, "Operation in Progress", "Cannot save while translations are active.")
                return
            if not self.data:
                QtWidgets.QMessageBox.warning(self, "Save Error", "No LORE-book data loaded to save.")
                return
            if self.is_dirty:
                self.save_all_changes()

            self.save_cache()
            
            try:
                data_to_export = copy.deepcopy(self.data)
            except Exception as e:
                logger.error(f"Failed to deepcopy data for export: {e}", exc_info=True)
                QtWidgets.QMessageBox.critical(self, "Save Error", f"An internal error occurred: {e}")
                return

            translations_exist = self._check_if_translations_exist()

            selected_languages = []
            include_originals = False
            
            if translations_exist:
                current_lore_name = os.path.splitext(os.path.basename(self.input_path))[0] if self.input_path else "New Lorebook"
                export_dialog = ExportSettingsDialog(
                    current_lore_name,
                    current_settings.get("target_languages", []),
                    self.translation_tab.current_target_language,
                    self)
                if export_dialog.exec() == QtWidgets.QDialog.Accepted:
                    lore_name_from_dialog, selected_languages, include_originals = export_dialog.get_export_settings()
                else:
                    logger.info("Save As operation cancelled by user in settings dialog.")
                    return
            else:
                logger.info("No translations found in cache for this LORE-book. Proceeding with direct save.")
                lore_name_from_dialog = os.path.splitext(os.path.basename(self.input_path))[0] if self.input_path else "New_LORE-book"

            src_lang = self.translation_tab.current_source_language
            if selected_languages:
                for entry_data in data_to_export['entries'].values():
                    self._ensure_entry_key_is_list(entry_data)
                    uid = entry_data.get('uid')
                    if uid is None: 
                        continue
                    
                    original_keys = list(entry_data.get('key', []))
                    final_keys = set(original_keys) if include_originals else set()
                    
                    found_any_translation = False
                    for lang in selected_languages:
                        for key_text in original_keys:
                            cache_key = self._generate_cache_key(uid, key_text, src_lang, lang)
                            if cache_key in self.cache:
                                translated_key = self.cache[cache_key]
                                if translated_key:
                                    final_keys.add(translated_key)
                                    found_any_translation = True
                    
                    if not include_originals and not found_any_translation:
                        final_keys.update(original_keys)

                    entry_data['key'] = sorted(list(final_keys))

            if self.input_path:
                start_dir = os.path.dirname(self.input_path)
            else:
                start_dir = os.path.expanduser("~")

            base_name = lore_name_from_dialog.replace(" ", "_")
            default_save_path = os.path.join(start_dir, f"{base_name}.json")

            output_path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save LORE-book As", default_save_path, "LORE-book (*.json);;All Files (*)")

            if not output_path:
                logger.info("Save As operation cancelled by user in file dialog.")
                return

            logger.info(f"Attempting to save LORE-book data to: {output_path}")
            self.status_bar.showMessage(f"Saving to {os.path.basename(output_path)}...")
            QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data_to_export, f, ensure_ascii=False, indent=2)

                self.input_path = output_path
                self.load_file(self.input_path)
                self.set_dirty_flag(False)
                QtWidgets.QMessageBox.information(self, 'Save Successful', f'The LORE-book has been saved to:\n{output_path}')

            except Exception as e:
                logger.error(f'Save failed for {output_path}: {e}', exc_info=True)
                QtWidgets.QMessageBox.critical(self, 'Save Error', f'Failed to save LORE-book: {e}')
            finally:
                QtWidgets.QApplication.restoreOverrideCursor()

    def _save_lorebook_data(self):
            if not self.input_path or not self.data:
                raise IOError("Cannot save LORE-book data: input path or data is missing.")

            data_to_save = {"entries": self.data.get("entries", {})}
            
            with open(self.input_path, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    def save_all_changes(self):
        if not self.is_dirty:
            logger.debug("save_all_changes called, but no changes to save (not dirty).")
            return

        if not self.input_path:
            logger.info("save_all_changes: input_path is None. Triggering export_lorebook to set a path.")
            self.export_lorebook()
            return

        logger.info(f"Saving all changes for {os.path.basename(self.input_path)}")
        self.status_bar.showMessage("Saving changes...", 2000)
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            self._save_lorebook_data()
            self.save_cache()

            self.set_dirty_flag(False)
            self.status_bar.showMessage("All changes saved.", 3000)
            logger.info("All changes successfully saved to disk.")

        except Exception as e:
            logger.error(f"Failed to save all changes: {e}", exc_info=True)
            QtWidgets.QMessageBox.critical(self, "Save Error", f"Could not save changes: {e}")
            self.status_bar.showMessage("Save failed!", 5000)
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()

    def closeEvent(self, event: QtGui.QCloseEvent):
            logger.info("Close event received.")

            if self.active_translation_jobs > 0:
                if QtWidgets.QMessageBox.question(self, "Confirm Exit", f"{self.active_translation_jobs} translation job(s) are still active. Exit anyway?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.No:
                    logger.info("Exit cancelled by user due to active jobs.")
                    if event: 
                        event.ignore()
                    return

            if self.is_dirty:
                logger.info("Unsaved changes detected on exit. Saving automatically...")
                self.save_all_changes()

            self._cancel_batch_translation(silent=True)
            
            self.save_cache()
            save_settings()
            
            logger.info("Settings and cache saved. Application closing.")
            
            if self.model_inspector_window: 
                self.model_inspector_window.close()
            
            global fh
            if fh:
                try: 
                    logger.removeHandler(fh)
                    fh.close()
                    fh = None
                except Exception as e_log: 
                    print(f"Error closing file log: {e_log}")
            
            if self.qt_log_handler:
                try: 
                    logger.removeHandler(self.qt_log_handler)
                    self.qt_log_handler = None
                except Exception as e_log_qt: 
                    print(f"Error removing Qt log handler: {e_log_qt}")
            
            if event: 
                event.accept()


def run_main_app():
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    try:
        icon_bytes = base64.b64decode(ICON_BASE64_DATA)
        pixmap = QtGui.QPixmap()
        pixmap.loadFromData(icon_bytes)
        app_icon = QtGui.QIcon(pixmap)
        app.setWindowIcon(app_icon)
        logger.debug("Successfully loaded embedded icon.")
    except Exception as e:
        logger.warning(f"Could not load embedded icon: {e}. Falling back to theme icon.")
        app.setWindowIcon(QtGui.QIcon.fromTheme("applications-education-translation", QtGui.QIcon.fromTheme("accessories-dictionary")))

    try:
        app.setStyleSheet(qdarktheme.load_stylesheet("dark"))
        logger.debug("Applied qdarktheme (dark).")

        custom_stylesheet = """
            QToolTip {
                color: #e0e0e0; 
                background-color: #3c3c3c; 
                border: 1px solid #555555; 
                padding: 5px; 
                border-radius: 4px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding-left: 10px;
                padding-right: 10px;
            }
        """
        current_stylesheet = app.styleSheet()
        app.setStyleSheet(current_stylesheet + custom_stylesheet)
        logger.debug("Applied custom stylesheets for QToolTip and QGroupBox titles.")

    except Exception as e_theme: 
        logger.warning(f"pyqtdarktheme not found or failed: {e_theme}. Using default OS theme.")

    if not current_settings.get("api_keys"):
        logger.warning("Gemini API Keys not found. Prompting user.")
        temp_parent = QtWidgets.QWidget()
        s_dialog = SettingsDialog(current_settings, temp_parent)
        if s_dialog.exec() == QtWidgets.QDialog.Accepted:
            current_settings.update(s_dialog.get_settings())
            save_settings()
            if not current_settings.get("api_keys"):
                QtWidgets.QMessageBox.critical(None, "API Key Error", "API Key(s) not provided. Exiting.")
                logger.critical("API Key(s) not provided after dialog. Exiting.")
                sys.exit(1)
            else:
                logger.info("API key(s) provided via initial dialog.")
        else:
            QtWidgets.QMessageBox.warning(None, "API Key Missing", "API Key(s) required. Exiting.")
            logger.warning("User cancelled API key input at startup. Exiting.")
            sys.exit(1)
        temp_parent.deleteLater()

    win = TranslatorApp()
    win.showMaximized()
    logger.info(f"Lorebook Gemini Translator v{APP_VERSION} started.")
    sys.exit(app.exec())

if __name__ == '__main__':
    custom_theme = Theme({ "log.time": "#29e97c", "logging.level.debug": "#11d9e7", "logging.level.info": "#0505f3", "logging.level.warning": "#FF00FF", "logging.level.error": "#FF0000", "logging.level.critical": "#FA8072"})
    class CombinedHighlighter(ReprHighlighter):
        def highlight(self, text):
            super().highlight(text)
            highlight_map = { r"(?i)\b(API)\b": "bold #ff2075", r"(?i)\b(Job|dispatch)\b": "bold #00ff88", r"(?i)\b(cache)\b": "italic #e786ff", r"(?i)\b(success|completed)\b": "bold #00af00", r"(?i)\b(failed|error)\b": "bold #ff0000", r"(?i)\b(warning)\b": "bold #ffaf00", r"(?i)\b(key|model)\b": "#d78700", r"(?i)\b(RPM|cooldown)\b": "#ecc1c1"}
            for pattern, style in highlight_map.items():
                text.highlight_regex(pattern, style=style)

    console = Console(theme=custom_theme)
    rich_handler = RichHandler( console=console, rich_tracebacks=True, show_path=False, highlighter=CombinedHighlighter(), log_time_format="[%Y-%m-%d %H:%M:%S.%f]" )
    logging.basicConfig(level="NOTSET", format="%(message)s", handlers=[rich_handler] )

    load_settings()

    app_log_level_str = current_settings.get("log_level", "INFO").upper()
    app_log_level_int = getattr(logging, app_log_level_str, logging.INFO)
    
    if app_log_level_int > logging.DEBUG:
        lib_level = logging.WARNING
        logger.debug("Application log level is INFO or higher. Suppressing library debug messages.")
    else:
        lib_level = logging.DEBUG
        logger.debug("Application log level is DEBUG. Showing library debug messages.")
    

    logging.getLogger('urllib3').setLevel(lib_level)
    logging.getLogger('google.api_core').setLevel(lib_level)
    logging.getLogger('google.auth').setLevel(lib_level)
    logging.getLogger('httpcore').setLevel(lib_level)

    check_and_trigger_update()

    from google import genai
    from google.genai import types, errors
    from google.api_core.exceptions import ResourceExhausted

    run_main_app()