import discord

class PermissionHelper:
    def __init__(self, perm_levels: dict):
        self.perm_levels = perm_levels

    def getUserPermLevel(self, member: discord.Member) -> int:
        maxlvl = 0
        for role in member.roles:
            maxlvl = max(maxlvl, self.perm_levels.get(role.id, 0))
        return maxlvl
    
    def isUserAbove(self, member: discord.Member, level: int) -> bool:
        return self.getUserPermLevel(member) >= level