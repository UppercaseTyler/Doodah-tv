# Channel logo sources

Official HTTPS image URLs selected for the private channel configuration. Some images are hosted by their owners; the four full-name PNGs listed below are bundled for HTTPS hosting through GitHub. Third-party artwork is excluded from Doodah’s GPL license; see [the artwork notice](../assets/logos/THIRD-PARTY.md). Checked November 9, 2026.

| Channels | Organization | HTTPS image |
| --- | --- | --- |
| 101 | Oakland Zoo Giraffes | [Image](https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/main/assets/logos/oakland-zoo.png) |
| 102, 103, 104 | Cheyenne Mountain Zoo | [Image](https://www.cmzoo.org/apple-touch-icon.png) |
| 105 | Victoria Zoo Giraffes | [Image](https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/main/assets/logos/melbourne-zoo.png) |
| 106 | Holnicote Estate Beaver Lodge | [Image](https://static.nationaltrust.org.uk/nt-front-end/images/apple-touch-icon.png) |
| 107 | Big Bear Bald Eagle Cam | [Image](https://friendsofbigbearvalley.org/wp-content/uploads/2025/08/Cleared-Logo-1.png) |
| 201 | Seattle Aquarium Otters | [Image](https://www.seattleaquarium.org/wp-content/uploads/2023/05/Seattle-Aquarium-favicon-300x300.png) |
| 202 | Moody Gardens Penguin Cam | [Image](https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/main/assets/logos/moody-gardens.png) |
| 203, 204, 205, 206, 207 | Georgia Aquarium | [Image](https://raw.githubusercontent.com/UppercaseTyler/Doodah-tv/main/assets/logos/georgia-aquarium.png) |
| 109, 110 | Toledo Zoo | [Image](https://www.toledozoo.org/apple-touch-icon.png) |
| 111 | Namib Desert Waterhole | Doodah default (no verified operator artwork selected) |

Oakland, Melbourne, Moody Gardens, and Georgia Aquarium use full-name artwork rendered from their official websites. Moody Gardens has a white background for contrast. Holnicote uses National Trust branding. Cheyenne retains its giraffe icon; Seattle, Toledo, and Big Bear retain their existing artwork. The new PNGs need to be pushed to GitHub before deploying their configuration URLs; Plex rendering still needs verification after deployment.

Missing or blank `logo` values and missing local files use the HTTPS Doodah logo. Remote URLs are passed through: a later outage or URL change at the image host does not automatically trigger fallback.
