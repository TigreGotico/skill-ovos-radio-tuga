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
               for ch in self.db.values() if ch.get("stream")]
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
    for r in s.ocp_radio_tuga_playlist("portuguese radio", MediaType.RADIO):
        print(r)
        # Playlist(title='Radios de Portugal (All stations)', artist='Radios de Portugal', position=0, image='https://radiotuga.com/img3/LoneDJsquare400.jpg', match_confidence=100, skill_id='t.fake', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', playback=<PlaybackType.AUDIO: 2>, media_type=<MediaType.RADIO: 7>)

    for r in s.search_radio_tuga("fado de coimbra", MediaType.RADIO):
        print(r)
        # MediaEntry(uri='https://nl.digitalrm.pt:8048/stream', title='Radio Fado de Coimbra', artist='Radios de Portugal', match_confidence=91, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/qhv8f3hhrspa.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://b0ne.hopto.org:8443/silveradio', title='Radio Live Concert', artist='Radios de Portugal', match_confidence=70, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://s1.stmxp.net:8046/;', title='Radio Dance Portugal', artist='Radios de Portugal', match_confidence=65, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://tonyvendas.top:8486/;', title='Radio Fonte Da Moura', artist='Radios de Portugal', match_confidence=65, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://s1.stmxp.net:8046/;', title='Radio Dance Portugal', artist='Radios de Portugal', match_confidence=65, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://radios.dotsi.pt:8020/;stream', title='Rádio Clube de Alcoutim RCA', artist='Radios de Portugal', match_confidence=64, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/jxwyqfmettza.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://radios.dotsi.pt:8020/;stream', title='Rádio Clube de Alcoutim RCA', artist='Radios de Portugal', match_confidence=64, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/jxwyqfmettza.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://138.201.198.218:8010/stream', title='Radio Marte Madeira', artist='Radios de Portugal', match_confidence=62, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://138.201.198.218:8010/stream', title='Radio Marte Madeira', artist='Radios de Portugal', match_confidence=62, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://sonic.servsonic.com:7020/;', title='Radio Estremadura', artist='Radios de Portugal', match_confidence=61, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/r76cwb6m9fnk.png', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://stream.zeno.fm/q9k377tdzy8uv', title='Saudade Cidade', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://stream.zeno.fm/fx5n4m0xkwzuv', title='Radio Despertar', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://hts08.kshost.com.br:11264/;', title='Radio EuroPub', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/341/radio-europub.35964f99.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://stream.zeno.fm/ornbvesigjlvv', title='Rádio Amor e Loucura', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='https://eu8.fastcast4u.com/proxy/jotajss?mp=/1', title='Radio Tematica', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://cdn.mytuner.mobi/static/ctr/images/radio-default.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
        # MediaEntry(uri='http://hts08.kshost.com.br:11264/;', title='Radio EuroPub', artist='Radios de Portugal', match_confidence=60, skill_id='t.fake', playback=<PlaybackType.AUDIO: 2>, status=<TrackState.DISAMBIGUATION: 1>, media_type=<MediaType.RADIO: 7>, length=-1, image='https://static.mytuner.mobi/media/radios-150px/341/radio-europub.35964f99.jpg', skill_icon='/home/miro/PycharmProjects/skill-ovos-radio-tuga/radios_pt.png', javascript='')
