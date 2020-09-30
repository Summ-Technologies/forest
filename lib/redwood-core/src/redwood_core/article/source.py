import re
from enum import Enum

from redwood_db.content import Subscription


class SourceType(Enum):
    GENERIC = "GENERIC"
    SUBSTACK = "SUBSTACK"


def source_to_source_type(from_address: str):
    if "@substack" in from_address:
        return SourceType.SUBSTACK
    else:
        return SourceType.GENERIC


def is_newsletter_subscription(
    from_address: str, from_name: str, subscription: Subscription
):
    if (
        re.search(subscription.from_address, from_address, re.IGNORECASE) is not None
        and re.search(subscription.name, from_name, re.IGNORECASE) is not None
    ):
        return True


def new_subscription(from_address: str, from_name: str = None):
    if from_name is None:
        from_name = ".*"
    return Subscription(from_address=from_address, name=from_name)


general_newsletter_subscriptions = [
    new_subscription(
        from_address="@substack.com",
    ),
    new_subscription(from_address="^hello@6pages.com$"),
    new_subscription(from_address="^austin@austinkleon.com$"),
    new_subscription(from_address="@axios.com"),
    new_subscription(from_address="^team@acciyo.com$"),
    new_subscription(from_address="^list@ben-evans.com$"),
    new_subscription(
        from_address="^newsletter@businessinsider.com$",
    ),
    new_subscription(from_address="^morningsquawk@response.cnbc.com$"),
    new_subscription(
        from_address="^politics@response.cnbc.com$",
    ),
    new_subscription(from_address="^kelly@cnbc.com$"),
    new_subscription(
        from_address="^editors@fiercebiotech.com$",
    ),
    new_subscription(from_address="^hello@finimize.com$"),
    new_subscription(
        from_address="^josh@connectedcomedy.com$",
    ),
    new_subscription(
        from_address="^kale@hackernewsletter.com$",
    ),
    new_subscription(from_address="^newsletter@jkglei.com$"),
    new_subscription(from_address="^jack@jack-clark.net$"),
    new_subscription(from_address="@launch.co"),
    new_subscription(from_address="^bob@lefsetz.com$"),
    new_subscription(from_address="^hello@mailbrew.com$"),
    new_subscription(from_address="^matt@othersideai.com$"),
    new_subscription(from_address="^crew@morningbrew.com$"),
    new_subscription(from_address="^hello@muckrack.com$"),
    new_subscription(from_address="^info@theneed2know.com$"),
    new_subscription(from_address="^email@nl.npr.org$"),
    new_subscription(from_address="^nytdirect@nytimes.com$"),
    new_subscription(from_address="^journalism@pewresearch.org$"),
    new_subscription(from_address="^politicoplaybook@email.politico.com$"),
    new_subscription(from_address="^hello@digest.producthunt.com$"),
    new_subscription(from_address="^hi@qz.com$"),
    new_subscription(
        from_address="^noreply@robinhood.com$", from_name="Robinhood Snacks"
    ),
    new_subscription(from_address="^edith@race.capital$"),
    new_subscription(from_address="^newsletter@techcrunch.com$"),
    new_subscription(from_address="^newsletters@technologyreview.com$"),
    new_subscription(from_address="^fortune@newsletters.fortune.com$"),
    new_subscription(from_address="^inside@thedailybeast.com$"),
    new_subscription(from_address="@pitchbook.com"),
    new_subscription(from_address="^news@thehustle.co$"),
    new_subscription(from_address="^hello@theinformation.com$"),
    new_subscription(from_address="^editors@SundayLongRead.com$"),
    new_subscription(
        from_address="^contact@theundefeated.com$",
    ),
    new_subscription(
        from_address="^dailyskimm@morning7.theskimm.com$",
    ),
    new_subscription(from_address="^tim@fourhourbody.com$"),
    new_subscription(from_address="^dan@tldrnewsletter.com$"),
    new_subscription(
        from_address="^team@marketing.angel.co$",
    ),
    new_subscription(from_address="^newsletter@vox.com$"),
]
