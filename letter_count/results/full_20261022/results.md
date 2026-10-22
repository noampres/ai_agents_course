# Letter-counting results

| dictionary | question | CoT prompt | thinking | claude-haiku-4-5 | claude-haiku-5-5 |
|---|---|---|---|---|---|
| he | he | no | no | 55% (55/100) | 100% (100/100) |
| he | he | no | yes | 100% (100/100) | 100% (100/100) |
| he | he | yes | no | 100% (100/100) | 100% (100/100) |
| he | he | yes | yes | 100% (100/100) | 100% (100/100) |
| he | en | no | no | 79% (79/100) | 98% (98/100) |
| he | en | no | yes | 100% (100/100) | 99% (99/100) |
| he | en | yes | no | 100% (100/100) | 100% (100/100) |
| he | en | yes | yes | 100% (100/100) | 100% (100/100) |
| en | he | no | no | 81% (81/100) | 96% (96/100) |
| en | he | no | yes | 100% (100/100) | 99% (99/100) |
| en | he | yes | no | 100% (100/100) | 100% (100/100) |
| en | he | yes | yes | 99% (99/100) | 100% (100/100) |
| en | en | no | no | 85% (85/100) | 89% (89/100) |
| en | en | no | yes | 100% (100/100) | 89% (89/100) |
| en | en | yes | no | 99% (99/100) | 100% (100/100) |
| en | en | yes | yes | 100% (100/100) | 100% (100/100) |

## By factor

| factor | value | accuracy |
|---|---|---|
| dict | en | 96% (1537/1600) |
| dict | he | 96% (1531/1600) |
| qlang | en | 96% (1538/1600) |
| qlang | he | 96% (1530/1600) |
| cot | no | 92% (1470/1600) |
| cot | yes | 100% (1598/1600) |
| thinking | no | 93% (1482/1600) |
| thinking | yes | 99% (1586/1600) |
| model | claude-haiku-4-5 | 94% (1498/1600) |
| model | claude-haiku-5-5 | 98% (1570/1600) |
