from os.path import join, dirname
from typing import Iterable

from json_database import JsonStorage
from ovos_utils import classproperty
from ovos_utils.parse import fuzzy_match, MatchStrategy
from ovos_utils.process_utils import RuntimeRequirements
from ovos_workshop.backwards_compat import MediaType, PlaybackType, MediaEntry, Playlist
from ovos_workshop.decorators.ocp import ocp_search, ocp_featured_media
from ovos_workshop.skills.common_play import OVOSCommonPlaybackSkill


class RadioTugaSkill(OVOSCommonPlaybackSkill):

    def __init__(self, *args, **kwargs):
        self.db = JsonStorage(f"{dirname(__file__)}/res/radios_pt.json")
        super().__init__(supported_media=[MediaType.MUSIC,
                                          MediaType.RADIO,
                                          MediaType.GENERIC],
                         skill_icon=join(dirname(__file__), "radios_pt.png"),
                         skill_voc_filename="radiotuga_skill",
                         *args, **kwargs)

    def initialize(self):
        # register with OCP to help classifier pick MediaType.RADIO
        self.register_ocp_keyword(MediaType.RADIO,
                                  "radio_station", [s["name"] for s in self.db.values()])
        self.register_ocp_keyword(MediaType.RADIO,
                                  "radio_streaming_provider",
                                  ["Radio Tuga", "Radio Portuguesa", "Radio de Portugal"])

    @classproperty
    def runtime_requirements(self):
        return RuntimeRequirements(internet_before_load=True,
                                   network_before_load=True,
                                   gui_before_load=False,
                                   requires_internet=True,
                                   requires_network=True,
                                   requires_gui=False,
                                   no_internet_fallback=False,
                                   no_network_fallback=False,
                                   no_gui_fallback=True)

    @ocp_featured_media()
    def featured_media(self) -> Playlist:
        pl = Playlist(media_type=MediaType.RADIO,
                      title="Radios de Portugal (All stations)",
                      playback=PlaybackType.AUDIO,
                      image="https://radiotuga.com/img3/LoneDJsquare400.jpg",
                      skill_id=self.skill_id,
                      artist="Radios de Portugal",
                      match_confidence=100,
                      skill_icon=self.skill_icon)
        pl += [MediaEntry(media_type=MediaType.RADIO,
                          uri=ch["stream"],
                          title=ch["name"],
                          playback=PlaybackType.AUDIO,
                          image=ch["image"],
                          skill_id=self.skill_id,
                          artist="Radios de Portugal",
                          match_confidence=90,
                          length=-1,  # live stream
                          skill_icon=self.skill_icon)
               for ch in self.db.values()]
        return pl

    @ocp_search()
    def ocp_radio_tuga_playlist(self, phrase: str, media_type: MediaType) -> Iterable[Playlist]:
        if self.voc_match(phrase, "radiotuga", exact=media_type != MediaType.RADIO):
            yield self.featured_media()

    @ocp_search()
    def search_radio_tuga(self, phrase, media_type) -> Iterable[MediaEntry]:
        base_score = 0

        if media_type == MediaType.RADIO:
            base_score += 20
        else:
            base_score -= 30

        if self.voc_match(phrase, "radio"):
            base_score += 10

        if self.voc_match(phrase, "radiotuga"):
            base_score += 30  # explicit request
            phrase = self.remove_voc(phrase, "radiotuga")

        results = []
        for ch in self.db.values():
            if not ch.get("stream"):
                continue
            score = round(base_score + fuzzy_match(ch["name"].lower(), phrase.lower(),
                                                   strategy=MatchStrategy.DAMERAU_LEVENSHTEIN_SIMILARITY) * 100)
            if score < 60:
                continue
            results.append(MediaEntry(media_type=MediaType.RADIO,
                             uri=ch["stream"],
                             title=ch["name"],
                             playback=PlaybackType.AUDIO,
                             image=ch["image"],
                             skill_id=self.skill_id,
                             artist="Radios de Portugal",
                             match_confidence=min(100, score),
                             length=-1,  # live stream
                             skill_icon=self.skill_icon))
        results.sort(key=lambda k: k.match_confidence, reverse=True)
        return results


if __name__ == "__main__":
    from ovos_utils.messagebus import FakeBus
    from ovos_utils.log import LOG

    LOG.set_level("DEBUG")

    s = RadioTugaSkill(bus=FakeBus(), skill_id="t.fake")
    #for r in s.ocp_radio_tuga_playlist("radiotuga", MediaType.RADIO):
    #    print(r)
        # Playlist(title='RadioTuga (All stations)', artist='RadioTuga', position=0, image='https://radiotuga.com/img3/LoneDJsquare400.jpg', match_confidence=100, skill_id='t.fake', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-radio-tuga/radios_pt.png', playback=<PlaybackType.AUDIO: 2>, media_type=<MediaType.RADIO: 7>)
    for r in s.search_radio_tuga("fado de coimbra", MediaType.RADIO):
        print(r)
        # MediaEntry(uri='http://ice2.radiotuga.com/beatblender-128-mp3', title='Beat Blender', artist='RadioTuga', match_confidence=62, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.radiotuga.com/logos/512/beatblender512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://ice2.radiotuga.com/deepspaceone-128-mp3', title='Deep Space One', artist='RadioTuga', match_confidence=66, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.radiotuga.com/logos/512/deepspaceone512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://ice2.radiotuga.com/illstreet-128-mp3', title='Illinois Street Lounge', artist='RadioTuga', match_confidence=61, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.radiotuga.com/logos/512/illstreet512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://ice2.radiotuga.com/secretagent-128-mp3', title='Secret Agent', artist='RadioTuga', match_confidence=100, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://api.radiotuga.com/logos/512/secretagent512.png', skill_icon='/home/miro/PycharmProjects/OCPSkills/skill-ovos-radio-tuga/radios_pt.png', javascript='')
