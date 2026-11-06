import sys,json
sys.path.insert(0,'/home/claude/mk')
from audio import make
specs={
 'v2':dict(dur=18.6,start_drop=0.37,events=[(0,'riser',.5),(0.37,'impact',1),(2.5,'whoosh',.6),(5.6,'pop',1),(7.2,'whoosh',.5),(10.1,'impact',1),(11.4,'pop',.7),(14.5,'pop',1),(15.6,'impact',.9),(16.4,'pop',.8)]),
 'v3':dict(dur=16.6,start_drop=0.05,events=[(0.05,'pop',.9),(0.47,'pop',.9),(0.89,'impact',1),(2.15,'whoosh',.7),(4.6,'pop',.6),(6.4,'pop',.8),(9.0,'pop',.6),(11.6,'impact',.9),(13.8,'whoosh',.7),(14.6,'pop',.8)]),
 'v4':dict(dur=16.4,start_drop=1.45,events=[(0.1,'riser',.5),(1.45,'impact',1),(2.55,'whoosh',.7),(3.0,'pop',.9),(3.7,'pop',.9),(4.7,'pop',.9),(5.3,'pop',.9),(6.1,'pop',.9),(6.95,'whoosh',.7),(7.9,'impact',.8),(10.75,'whoosh',.7),(11.5,'pop',.7),(13.6,'impact',.9)]),
 'v5':dict(dur=16.4,start_drop=0.81,events=[(0.05,'pop',.8),(0.43,'pop',.8),(0.81,'impact',1),(2.45,'whoosh',.7),(3.0,'pop',.6),(5.75,'whoosh',.7),(8.95,'whoosh',.7),(9.4,'pop',.6),(11.85,'pop',.9),(12.3,'pop',.9),(12.75,'impact',1),(13.6,'impact',.8)]),
 'v6':dict(dur=16.6,start_drop=0.4,events=[(0.05,'pop',.8),(0.4,'impact',1),(1.1,'pop',.8),(2.0,'impact',.8),(4.4,'impact',.8),(6.8,'impact',.8),(9.2,'impact',.8),(11.6,'impact',.8),(13.8,'impact',.9)]),
 'v7':dict(dur=25.0,start_drop=0.2,events=[(0.0,'riser',.4),(0.2,'impact',1),(0.55,'pop',.8),(0.85,'pop',.8),(1.15,'pop',.8),(1.5,'pop',.6),(2.4,'whoosh',.8),(2.45,'impact',.8),(3.65,'pop',.9),(5.8,'whoosh',.8),(6.4,'pop',.5),(8.0,'whoosh',.7),(8.05,'impact',.7),(9.4,'whoosh',.8),(9.73,'pop',.9),(9.8,'pop',.6),(10.6,'pop',.9),(11.1,'impact',1),(12.8,'whoosh',.8),(13.13,'pop',.9),(13.2,'pop',.6),(14.0,'pop',.9),(14.5,'impact',1),(16.2,'whoosh',.8),(17.6,'riser',.4),(17.7,'pop',.8),(17.9,'pop',.7),(18.1,'pop',.7),(18.2,'impact',.8),(19.0,'impact',.8),(20.2,'impact',.8),(21.4,'impact',.8),(22.6,'impact',1)]),
 'v1':dict(dur=16,start_drop=1.0,events=[(0,'riser',.6),(1.0,'impact',1),(2.55,'whoosh',.8),(3.15,'pop',.8),(5.2,'pop',.8),(6.95,'whoosh',.8),(7.9,'pop',1),(10.35,'whoosh',.8),(10.9,'pop',.8),(12.3,'riser',.7),(13.4,'impact',1)]),
}
if __name__=='__main__':
    for k in sys.argv[1:]:
        sp=specs[k];make(f'/home/claude/mk/audio/{k}.wav',sp['dur'],sp['events'],start_drop=sp.get('start_drop',0));print(k)
