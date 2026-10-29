"""Approximate tournament host macro regions."""

from promcs.liquipedia.parse import clean

INTERNATIONAL_COUNTRIES = {"World", "International", "Global", "Americas"}

_REGION_NAMES = {
    "EU": "Europe, Sweden, United Kingdom, Poland, Germany, Portugal, Finland, Denmark, Czech Republic, Romania, France, Spain, Netherlands, Norway, Belgium, Italy, Hungary, Serbia, Bulgaria, Slovakia, Greece, Austria, Switzerland, Croatia, Estonia, Latvia, Lithuania, Ireland, Bosnia and Herzegovina, Slovenia, Montenegro, North Macedonia, Albania, Kosovo, Iceland, Malta, Cyprus, Luxembourg, Turkey, Israel, Balkans, Nordic, Scandinavia, Baltics, Western Europe, Eastern Europe, Central Europe, Northern Europe, Southern Europe, DACH, Iberia, Benelux, Nordic Countries, eu",
    "CIS": "Russia, Ukraine, CIS, Kazakhstan, Central Asia, Uzbekistan, Belarus, Kyrgyzstan, Georgia, Armenia, Azerbaijan, Moldova, Tajikistan",
    "SA": "South America, Brazil, Argentina, Chile, Peru, Colombia, Uruguay, Paraguay, Bolivia, Ecuador, Venezuela, Latin America",
    "NA": "North America, United States, Canada, Mexico, Central America, Latin America North",
    "AS": "China, Asia, Mongolia, India, Japan, South Korea, Korea, Taiwan, Hong Kong, Singapore, Malaysia, Indonesia, Philippines, Thailand, Vietnam, Southeast Asia, East Asia, South Asia, Middle East, Saudi Arabia, United Arab Emirates, Qatar, Kuwait, Jordan, Lebanon, Pakistan, Bangladesh, Sri Lanka, Nepal, MENA, Iran, Iraq, Egypt, Asia-Pacific, APAC, West Asia, Arabia, Levant, Syria, uae, Brunei, Myanmar",
    "OCE": "Oceania, Australia, New Zealand",
    "AF": "South Africa, Africa, Nigeria, Kenya, Morocco, Tunisia, Algeria, North Africa, Sub-Saharan Africa, Mauritius",
}
REGIONS = {
    name.strip(): code
    for code, names in _REGION_NAMES.items()
    for name in names.split(",")
}


def region(country):
    return REGIONS.get(clean(country)) if country else None
