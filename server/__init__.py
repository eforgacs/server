import asyncio
from asyncio import AbstractEventLoop
from .gameconnection import GameConnection
from .natpacketserver import NatPacketServer

import config
from server.lobbyconnection import LobbyConnection
from server.servercontext import ServerContext
from server.players import PlayersOnline
from server.games_service import GamesService


def run_lobby_server(address: (str, int),
                     player_service: PlayersOnline,
                     games: GamesService,
                     db,
                     loop: AbstractEventLoop=asyncio.get_event_loop()):
    """
    Run the lobby server

    :param address: Address to listen on
    :param player_service: Service to talk to about players
    :param games: Service to talk to about games
    :param db: Database
    :param loop: Event loop to use
    :return ServerContext: A server object
    """
    def initialize_connection(protocol):
        conn = LobbyConnection()
        conn.on_connection_made(protocol, protocol.writer.get_extra_info('peername'))
        return conn
    ctx = ServerContext(initialize_connection, loop)
    return ctx.listen(address[0], address[1])


def run_game_server(address: (str, int),
                    player_service: PlayersOnline,
                    games: GamesService,
                    db,
                    loop: AbstractEventLoop=asyncio.get_event_loop()):
    """
    Run the game server

    :return (NatPacketServer, ServerContext): A pair of server objects
    """
    nat_packet_server = NatPacketServer(loop, config.LOBBY_UDP_PORT)

    def initialize_connection(protocol):
        gc = GameConnection(loop, player_service, games, db)
        gc.on_connection_made(protocol, protocol.writer.get_extra_info('peername'))
        nat_packet_server.subscribe(gc, ['ProcessServerNatPacket'])
        return gc
    ctx = ServerContext(initialize_connection, loop)
    server = ctx.listen(address[0], address[1])
    return nat_packet_server, server
