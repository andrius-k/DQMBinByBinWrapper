import os
import re
import shutil
import argparse
import subprocess

def setup_cmssw():
    subprocess.call('cd CMSSW/CMSSW_10_6_0_pre3/src/ ; eval `scramv1 runtime -sh`', shell=True)

def create_temp_dir(pr_number, job_id):
    path = os.path.join('output', pr_number, job_id)
    subprocess.check_output(['mkdir', '-p', path])
    return path

def remove_temp_dir(pr_number, job_id):
    path = os.path.join(pr_number, job_id)
    shutil.rmtree(path, ignore_errors=True)

def download_base(input_path, release, architecture, real_arch):
    base_url = 'https://cmssdt.cern.ch/SDT/jenkins-artifacts/ib-baseline-tests/%s/%s/%s/matrix-results/' % (release, architecture, real_arch)
    download_root_files(input_path, base_url, is_base=True)

def download_pr(input_path, pr_number, job_id):
    base_url = 'https://cmssdt.cern.ch/SDT/jenkins-artifacts/pull-request-integration/PR-%s/%s/runTheMatrix-results/' % (pr_number, job_id)
    download_root_files(input_path, base_url, is_base=False)

def download_root_files(input_path, base_url, is_base):
    cookies_path = os.path.join(input_path, 'cookie.txt')

    command = ['cern-get-sso-cookie', '-o', cookies_path, '--url', base_url]
    subprocess.check_output(command)

    command = ['curl', '-L', '-s', '-k', '-b', cookies_path, '--url', base_url]
    output = subprocess.check_output(command)

    workflows = get_workflow_dirs(output)

    files_to_download = []

    for workflow in workflows:
        command = ['curl', '-L', '-s', '-k', '-b', cookies_path, '--url', os.path.join(base_url, workflow)]
        output = subprocess.check_output(command)
        dqm_file = get_dqm_file(output)

        if dqm_file:
            files_to_download.append(os.path.join(workflow, dqm_file))

    for file in files_to_download:
        url = os.path.join(base_url, file)
        local_dir = os.path.join(input_path, 'base' if is_base else 'pr', file)
        command = ['curl', '-L', '-s', '-k', '-b', cookies_path, '--url', url, '--output', local_dir, '--create-dirs']
        subprocess.check_output(command)
        print('Downloaded file: %s' % local_dir)

def run_comparison(input_path, pr_number, job_id, release):
    command = ['compareDQMOutput.py',
        '-b', 'output/%s/%s/base/' % (pr_number, job_id),
        '-p', 'output/%s/%s/pr/' % (pr_number, job_id),
        '-j', '1',
        '-n', pr_number,
        '-t', job_id,
        '-r', release,
        '-o', 'output/%s/%s/bbboutput' % (pr_number, job_id),
        '-s', 'output/%s/%s/' % (pr_number, job_id)]
    output = subprocess.check_output(command)
    print(output)

def get_workflow_dirs(html):
    matches = re.findall(r'[0-9]+\.[0-9]+_[^/]*/\">', html)
    matches = map(lambda x: x[:-2], matches)
    return matches

def get_dqm_file(html):
    matches = re.findall(r'DQM.*\.root">', html)

    if len(matches) > 0:
        return matches[0][:-2]
    else:
        return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This tool download baseline and PR files from cms bot and runs the bin by bin comparison.')
    parser.add_argument('-a', '--architecture', help='Baseline architecture. Sample: slc7_amd64_gcc700', required=True)
    parser.add_argument('-r', '--release', help='Baseline release format. Sample: CMSSW_10_6_X_2019-04-16-1100', required=True)
    parser.add_argument('-p', '--pr-number', help='PR number under test', required=True)
    parser.add_argument('-j', '--job-id', help='Unique test number to distinguish different comparisons of the same PR.', required=True)
    parser.add_argument('-ra', '--real-arch', help='Sample: -GenuineIntel', required=True)
    parser.add_argument('-o', '--output-dir', help='Comparison output directory', default='output')
    args = parser.parse_args()

    setup_cmssw()
    input_path = create_temp_dir(args.pr_number, args.job_id)
    # download_base(input_path, args.release, args.architecture, args.real_arch)
    # download_pr(input_path, args.pr_number, args.job_id)
    run_comparison(input_path, args.pr_number, args.job_id, args.release)
    # remove_temp_dir(args.pr_number, args.job_id)


