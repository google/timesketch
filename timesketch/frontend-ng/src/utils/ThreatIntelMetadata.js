const IOCTypes = [
    { regex: /^(\/[\S]+)+$/i, type: 'fs_path', humanReadable: 'Filesystem path' },
    { regex: /^([-\w]+\.)+[a-z]{2,}$/i, type: 'hostname', humanReadable: 'Hostname' },
    {
      regex: /^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/g,
      type: 'ipv4',
    },
    { regex: /^[0-9a-f]{64}$/i, type: 'hash_sha256', humanReadable: 'SHA256' },
    { regex: /^[0-9a-f]{40}$/i, type: 'hash_sha1', humanReadable: 'SHA1' },
    { regex: /^[0-9a-f]{32}$/i, type: 'hash_md5', humanReadable: 'MD5' },
    // Match any "other" selection
    { regex: /./g, type: 'other', humanReadable: 'Other' },
]

export {IOCTypes}
