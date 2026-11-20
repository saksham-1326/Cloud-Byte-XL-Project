"""Explicit admin CLI: python -m backend.ai_intelligence.cli migrate|sync ..."""
import argparse
import json
from backend.app import get_db_connection
from .migrations import migrate
from .store import Store
from .github import ActionsClient
from .collector import synchronize


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['migrate','sync','train','rca','worker'])
    parser.add_argument('--repository',default='saksham-1326/cloud-byte-xl-project')
    parser.add_argument('--run-id',type=int)
    parser.add_argument('--attempt',type=int,default=1)
    args=parser.parse_args()
    store=Store(get_db_connection)
    if args.command=='migrate':
        migrate(get_db_connection);print('AI schema migrations applied transactionally.');return
    if args.command=='sync':
        print(json.dumps(synchronize(ActionsClient(),store,args.repository),default=str,indent=2));return
    from .service import IntelligenceService
    service=IntelligenceService(store,ActionsClient())
    if args.command=='worker':
        service.worker();return
    result=service.train(args.repository) if args.command=='train' else service.rca(args.repository,args.run_id,args.attempt)
    print(json.dumps(result,default=str,indent=2))


if __name__=='__main__':
    main()
