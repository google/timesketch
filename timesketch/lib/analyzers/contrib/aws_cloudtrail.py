"""Sketch analyzer plugin for aws cloudtrail."""

from __future__ import unicode_literals

import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

logger = logging.getLogger("timesketch.analyzers.aws_cloudtrail")


class AwsCloudtrailSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for AwsCloudtrail."""

    NAME = "aws_cloudtrail"
    DISPLAY_NAME = "AWS CloudTrail Analyzer"
    DESCRIPTION = (
        "Extract features and tag security relevant actions in AWS CloudTrail."
    )

    DEPENDENCIES = frozenset()

    CLOUD_TRAIL_EVENT = "cloud_trail_event"
    EVENT_NAME = "event_name"

    def _cloudtrail_add_tag(self, event):
        cloud_trail_event = event.source.get(self.CLOUD_TRAIL_EVENT)
        event_name = event.source.get(self.EVENT_NAME)

        if cloud_trail_event:
            if '"readOnly":true' in cloud_trail_event:
                event.add_tags(["readOnly"])
                event.add_emojis([emojis.get_emoji("MAGNIFYING_GLASS")])

            if any( s in cloud_trail_event for s in ["UnauthorizedOperation", "AccessDenied"]):
                event.add_tags(["UnauthorizedAPICall"])

            if (
                '"userName":"HIDDEN_DUE_TO_SECURITY_REASONS"' in cloud_trail_event
                and '"errorMessage":"No username found in supplied account"' in cloud_trail_event
            ):
                event.add_tags(["FailedLoginNonExistentIAMUser"])

        if event_name:
            if event_name in (
                "AuthorizeSecurityGroupIngress",
                "AuthorizeSecurityGroupEgress",
                "RevokeSecurityGroupIngress",
                "RevokeSecurityGroupEgress",
                "CreateSecurityGroup",
                "DeleteSecurityGroup",
            ):
                event.add_tags(["SG"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateNetworkAcl",
                "CreateNetworkAclEntry",
                "DeleteNetworkAcl",
                "DeleteNetworkAclEntry",
                "ReplaceNetworkAclEntry",
                "ReplaceNetworkAclAssociation",
            ):
                event.add_tags(["NACL"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateCustomerGateway",
                "DeleteCustomerGateway",
                "AttachInternetGateway",
                "CreateInternetGateway",
                "DeleteInternetGateway",
                "DetachInternetGateway",
            ):
                event.add_tags(["GW"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateRoute",
                "CreateRouteTable",
                "ReplaceRoute",
                "ReplaceRouteTableAssociation",
                "DeleteRouteTable",
                "DeleteRoute",
                "DisassociateRouteTable",
            ):
                event.add_tags(["RouteTable"])
                event.add_tags(["NetworkChanged"])
            if event_name in (
                "CreateVpc",
                "DeleteVpc",
                "ModifyVpcAttribute",
                "AcceptVpcPeeringConnection",
                "CreateVpcPeeringConnection",
                "DeleteVpcPeeringConnection",
                "RejectVpcPeeringConnection",
                "AttachClassicLinkVpc",
                "DetachClassicLinkVpc",
                "DisableVpcClassicLink",
                "EnableVpcClassicLink",
            ):
                event.add_tags(["VPC"])
                event.add_tags(["NetworkChanged"])

            if event_name in (
                "PutGroupPolicy",
                "PutRolePolicy",
                "PutUserPolicy",
                "AttachGroupPolicy",
                "AttachRolePolicy",
                "AttachUserPolicy",
                "CreatePolicyVersion",
                "SetDefaultPolicyVersion",
                "AddUserToGroup",
                "CreateLoginProfile",
                "UpdateLoginProfile",
                "CreateAccessKey",
                "CreateRole",
                "AssumeRole",
            ):
                event.add_tags(["SuspicousIAMActivity"])

            if event_name in ("ConsoleLogin"):
                event.add_tags(["ConsoleLogin"])

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'data_type:"aws:cloudtrail:entry"'

        return_fields = [self.CLOUD_TRAIL_EVENT, self.EVENT_NAME]

        # Generator of events based on your query.
        # Swap for self.event_pandas to get pandas back instead of events.
        events = self.event_stream(query_string=query, return_fields=return_fields)

        # TODO: If an emoji is needed fetch it here.

        # TODO: Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # (If you add a view, please make sure the analyzer has results before
        # adding the view.)
        # view = sketch.add_view(
        #     view_name=name, analyzer_name=self.NAME,
        #     query_string=query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event_add_label('label')
        # event.add_star()
        # event.add_comment('comment')
        # event.add_emojis([my_emoji])
        # event.add_human_readable('human readable text', self.NAME)
        # Remember you'll need to add event.commit() once all changes to the
        # event have been completed.
        # You can also add a story.
        # story = self.sketch.add_story(title='Story from analyzer')
        # story.add_text('## This is a markdown title')
        # story.add_view(view)
        # story.add_text('This is another paragraph')
        for event in events:
            self._cloudtrail_add_tag(event)

        return "AWS CloudTrail Analyzer completed"


manager.AnalysisManager.register_analyzer(AwsCloudtrailSketchPlugin)
