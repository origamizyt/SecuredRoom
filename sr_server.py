from channel import Server, config
import service, sys

args = service.parse_args()
if args.anyIn('h', 'help'):
    print('Usage #1: python sr_server.py '
    '[-g | --backlog <value>] '
    '[-m | --msglen <value>]\n\t\t'
    '[-b | --between <value>] '
    '[-q | --quiet]')
    print('Usage #2: python sr_server.py [-h | --help]')
    sys.exit()
value = args.choices('b', 'backlog')
if value:
    config['MinBetween'] = float(value)
value = args.choices('m', 'msglen')
if value:
    config['MaxMessageLength'] = int(value)
value = args.choices('g', 'backlog')
if value:
    config['BacklogSize'] = int(value)
if not args.anyIn('q', 'quiet'):
    service.log_init()

service.log('正在启动服务器...')
s = Server(5000)
s.serve(True)
service.wait_forever()
service.log('服务器已关闭。')