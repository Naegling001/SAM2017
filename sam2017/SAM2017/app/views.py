from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.views.generic.edit import FormView, CreateView, UpdateView
from django.views.generic import View
from .models import Paper, SAM2017User, Notification, PCMAssign, PCMPickList, UserNotification, PCMReview, PCCReview,Deadline, NotificationTemplate
from .forms import DocumentForm, RegisterUser, ChangePasswordForm, ReuploadForm, UpdateProfileForm, PCMReviewForm, PCCReviewForm
from django.contrib import messages
from math import sqrt
import datetime

# for whatever reason, the 'user test' functions need to be defined before the
# request handler that uses them
def pcc_check(user):
    return user.groups.filter(name='PCC').exists()

def not_author_check(user):
    return user.groups.filter(name='PCC').exists() or user.groups.filter(name='PCM').exists()

def right_pcm(user, paper_id):
    return PCMAssign.objects.filter(pcm__user=user, paper__id = paper_id).exists()

def paper_author(user, paper_id):
    return Paper.objects.filter(contact_author__user=user, pk=paper_id).exists()

# Create your views here.
class RegisterUser(CreateView):
    template_name = 'app/register_user.html'
    form_class = RegisterUser
    success_url = ''

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        if form.is_valid():


            new_user = User(
                        first_name = request.POST['first_name'],
                        last_name = request.POST['last_name'],
                        email = request.POST['email'],
                        username = request.POST['username'],
                        password = request.POST['password'],
            )
            new_user.is_active = True
            new_user.set_password(new_user.password)
            new_user.save()
            author_group = Group.objects.get(name='Author')
            new_user.groups.add(author_group)
            SAM2017User.objects.get_or_create(user=new_user)[0]

            # new_user = form.save(commit = False)

            #new_user.set_password(new_user.password)
            # new_user.save()
            return HttpResponseRedirect('/app')

        return render(request, self.template_name, {'form': form})

# @login_required
class ChangePassword(CreateView):

    template_name = 'app/change_password.html'
    form_class = ChangePasswordForm
    success_url = ''

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        if form.is_valid():
            user = authenticate(username=request.user.username, password= request.POST['current_password'])
            if user is None:
                messages.add_message(request, messages.INFO, "The password was incorrect.")
                return (HttpResponseRedirect(''))

            current_user = User.objects.get(id = request.user.id)
            current_user.set_password(request.POST['password'])
            current_user.save()
            return HttpResponseRedirect('/app')

        return render(request, self.template_name, {'form': form})


# @login_required
class UpdateProfile(CreateView):

    template_name = 'app/update_profile.html'
    form_class = UpdateProfileForm
    success_url = ''

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form , 'user': request.user, 'fname': request.user.first_name, 'lname': request.user.last_name})

    def post(self, request, *args, **kwargs):

        form = self.form_class(request.POST)
        if form.is_valid():

            current_user = User.objects.get(id = request.user.id)
            current_user.first_name = request.POST['first_name']
            current_user.last_name = request.POST['last_name']
            current_user.email = request.POST['email']
            current_user.save()

            return HttpResponseRedirect('/app')

        return render(request, self.template_name, {'form': form})

@login_required
@user_passes_test(not_author_check, login_url='/app/upload/')
def index(request):
    paper_list = Paper.objects.order_by('-date_submitted')
    context_dict = {'papers': paper_list}
    can_download = []

    user_group = identify_user_group(request.user)
    if(user_group == 'PCM'):
        for paper in paper_list:
            if right_pcm(request.user, paper.id):
                can_download.append(paper.id)

    context_dict['user_group'] = user_group
    context_dict['can_download'] = can_download

    return render(request, 'app/index.html', context_dict)

def identify_user_group(user):
    group = ''
    if(user.groups.filter(name='Author').exists()):
        group = 'Author'
    elif(user.groups.filter(name='PCM').exists()):
        group = 'PCM'
    elif(user.groups.filter(name='PCC').exists()):
        group = 'PCC'
    else:
        group = 'undefined'

    return group

def user_login(request):
    context = RequestContext(request)

    if request.method == 'POST':
        un = request.POST.get('username')
        pw = request.POST.get('password')

        user = authenticate(username = un, password = pw)

        if user is not None:
            if user.is_active:
                login(request, user)
                return (HttpResponseRedirect('/app/'))
            else:
                return( HttpResponse( "Your account is disabled."))
        else:
            context['error_message'] = "Invalid login details";
            return(render(request, 'app/login.html', context))
    else:
        return(render(request, 'app/login.html', {}))

@login_required
def user_logout(request):
    logout(request)

    return HttpResponseRedirect('/app/')

@login_required
@user_passes_test(pcc_check, login_url='/app/upload/')
def assign(request, paper_id):
    paper1 = get_object_or_404(Paper, pk=paper_id)
    user_list = SAM2017User.objects.all()
    wishers = []
    subtract_from_pcm = 0

    try:
        wishlist = PCMPickList.objects.filter(paper=paper1)
        for wish in wishlist:
            wishers.append(wish.pcm.id)

    except ObjectDoesNotExist:
        wishers = null

    all_pcm = []
    pcm_id_selected = []

    for user in user_list:
        if user.user.groups.filter(name='PCM').exists():
            if(Paper.pcm_is_not_author(user, paper1)):
                all_pcm.append(user)

    num_pcms = len(all_pcm)
    print(str(num_pcms))
    context_dict = {'paper': paper1, 'pcm_list': all_pcm, 'wishers': wishers}

    if request.method == 'POST':
        for x in range(1, num_pcms + 1):
            if 'pcm'+str(x) in request.POST:
                pcm_id_selected.append(request.POST['pcm'+str(x)])

        if (len(pcm_id_selected) != 3):
            context_dict['error_message'] = "You must choose 3 PCM's"
        else:
            for z in range(3):
                pcm_obj = get_object_or_404(SAM2017User, pk=pcm_id_selected[z])
                pcm_assignment = PCMAssign(paper=paper1, pcm=pcm_obj)
                pcm_assignment.save()

            note = Notification(text = 'You have been assigned to review '+paper1.title)
            note.save()
            spread_pcm_assign_notification(note, pcm_id_selected)

            return HttpResponseRedirect(reverse('app:index'))
    elif (hasThreePCMs(paper1.id)):
        context_dict['error_message'] = "Three PCM's already assigned"
        context_dict['pcm_list'] = ''
    elif(num_pcms < 3):
        context_dict['pcm_list'] = ''

    return render(request, 'app/assign.html', context_dict)

def hasThreePCMs(paper_id):
    pcms = PCMAssign.objects.filter(paper__id=paper_id)
    return len(pcms) == 3

def calc_letter_grade(int_grade):
    letter_grade = ''

    if int_grade <= 60:
        letter_grade = 'F'
    elif int_grade < 62.5:
        letter_grade = 'D-'
    elif int_grade < 67.5:
        letter_grade = 'D'
    elif int_grade < 70:
        letter_grade = 'D+'
    elif int_grade < 72.5:
        letter_grade = 'C-'
    elif int_grade < 77.5:
        letter_grade = 'C'
    elif int_grade < 80:
        letter_grade = 'C+'
    elif int_grade < 82.5:
        letter_grade = 'B-'
    elif int_grade < 87.5:
        letter_grade = 'B'
    elif int_grade < 90:
        letter_grade = 'B+'
    elif int_grade < 92.5:
        letter_grade = 'A-'
    else:
        letter_grade = 'A'

    return letter_grade

def calc_std_deviation(numbers, mean):
    y = 0
    x = []
    sum = 0
    avg = 0

    for number in numbers:
        y = number - mean
        x.append(y*y)

    for z in x:
        sum += z

    avg = float(sum) / len(x)
    return sqrt(avg)

class UploadPaper(View):
    err = ''
    template_name = 'app/upload.html'
    form_class = DocumentForm() # A empty, unbound form

    def post(self, request, *args, **kwargs):
        current_user = request.user
        sam2017_user = SAM2017User.objects.get(user=current_user)
        # Load documents for the list page
        papers = Paper.objects.filter(contact_author=sam2017_user)
        form = DocumentForm(request.POST, request.FILES)
        title = request.POST['title']
        authors = request.POST['authors']
        if (form.is_valid() and Paper.isRightExt(request.FILES['docfile'].name)):
            newdoc = Paper(
                        docfile = request.FILES['docfile'],
                        title = request.POST['title'],
                        revision = False,
                        contact_author = sam2017_user,
                        authors = request.POST['authors'],
                        format = request.POST['format'],
            )
            newdoc.save()
            # get the template for the notification
            template = NotificationTemplate.objects.filter(type=1).last()
            notification1 = Notification(
                    text = get_note_from_template(template, [title, authors])
            )
            notification1.save()
            spread_submitted_notification(notification1, newdoc, sam2017_user)

            # create deadline notification
            template = NotificationTemplate.objects.filter(type=2).last()
            due_date = timezone.now()+datetime.timedelta(days=5)
            notification1 = Notification(
                    text= get_note_from_template(template, [due_date.strftime("%A %d, %B %Y")])
            )
            notification1.save()
            user_note = UserNotification(user = sam2017_user, notification = notification1)
            user_note.save()
            deadline = Deadline(date=due_date, notification=user_note)
            deadline.save()

        elif form.is_valid():
            self.err = 'The paper is not a PDF or Microsoft Word type.'
        else:
            self.err = 'form invalid'
        # Redirect to the document list after POST
        return render(request, self.template_name, {'papers': papers, 'form': self.form_class,'error_message':self.err})

    def get(self, request, *args, **kwargs):
        current_user = request.user
        sam2017_user = SAM2017User.objects.get(user=current_user)
        # Load documents for the list page
        papers = Paper.objects.filter(contact_author=sam2017_user)
        return render(request, self.template_name,{'papers': papers, 'form': self.form_class})

@login_required
def pcm_review(request, paper_id):

#   check if pcm was assigned to this paper
    if(not right_pcm(request.user, paper_id)):
        return redirect('/app/')

    paper1 = Paper.objects.get(pk=paper_id)
    curr_pcm = SAM2017User.objects.get(user__id=request.user.id)
    prev_pcm_review = ''
    review_redux = True

    try:
        prev_pcm_review = PCMReview.objects.get(pcm__user__id=curr_pcm.user.id, paper__id=paper_id)
    except ObjectDoesNotExist:
        review_redux = False


    if(request.method == 'POST'):
        if(review_redux):
            prev_pcm_review.grade = request.POST['grade']
            prev_pcm_review.comment = request.POST['comment']
            prev_pcm_review.save()
        else:
            review = PCMReview(
                pcm = curr_pcm,
                paper = paper1,
                grade = request.POST['grade'],
                comment = request.POST['comment']
            )
            review.save()

        if(PCMReview.is_last_review(paper1)):
            notification = Notification(
                text = 'The report for "'+paper1.title+'" is ready'
            )
            notification.save()
            spread_report_ready_notification(notification)

        return redirect('/app/')

    if(review_redux):
        form = PCMReviewForm(initial={'grade': prev_pcm_review.grade, 'comment': prev_pcm_review.comment})
    else:
        form = PCMReviewForm()

    return render(request, 'app/pcmreview.html', {'paper': paper1, 'form': form})

@login_required
@user_passes_test(pcc_check, login_url='/app/')
def pcc_review(request, paper_id):
    total = 0
    letter_grade = 'F'
    numbers = []
    warning = ''
    paper = Paper.objects.get(pk=paper_id)
    pcmreviews = PCMReview.objects.filter(paper__id=paper.id)

    if(request.method == 'POST'):
        if(request.POST['submit'] == 'Submit Review'):
            review = PCCReview(
                pcc = SAM2017User.objects.get(user__id=request.user.id),
                paper = Paper.objects.get(pk=paper_id),
                final_grade = request.POST['grade'],
                comment = request.POST['comment']
            )
            review.save()
            note = Notification(text = 'The grade for "'+paper.title+'" is ready to be viewed')
            note.save()
            user_note = UserNotification(user = SAM2017User.objects.get(pk = paper.contact_author.id), notification = note)
            user_note.save()

        else:
            notification = Notification (
                text = 'Reviews for paper "'+paper.title+'" are conflicting. PCM emails are '+pcmreviews[0].pcm.user.email+', '+pcmreviews[1].pcm.user.email+', and '+pcmreviews[2].pcm.user.email
            )
            notification.save()
            spread_resolve_conflict_notification(notification, [pcmreviews[0].pcm, pcmreviews[1].pcm, pcmreviews[2].pcm] )

        return redirect('/app/')

    if len(pcmreviews) < 3:
        return redirect('/app/')
    else:
        for review in pcmreviews:
            total += int(review.grade)
            numbers.append(int(review.grade))

        avg = float(total) / len(pcmreviews)
        avg = round(avg, 2)
        letter_grade = calc_letter_grade(avg)
        form = PCCReviewForm(initial={"grade": letter_grade})
        std_dev = calc_std_deviation(numbers, avg)
        std_dev = round(std_dev, 2)

        if std_dev > 10:
            warning = 'Warning, reviews are conflicting. Please suggest PCM\'s modify their reviews.'

    return render(request, 'app/pccreview.html', {'paper': paper, 'form': form, 'pcmreviews': pcmreviews, "avg": avg, "letter_grade": letter_grade, 'warning': warning})

@login_required
def report(request, paper_id):
    context = {}

    if (not paper_author(request.user, paper_id)):
        return redirect('/app/')

    if (not PCCReview.objects.filter(paper__id=paper_id).exists()):
        context['message'] = 'The report for this paper is not available at this time.'
    else:
        pcm_reviews = PCMReview.objects.filter(paper__id=paper_id)
        pcc_review = PCCReview.objects.get(paper__id=paper_id)
        paper = Paper.objects.get(pk=paper_id)
        context['pcm_reviews'] = pcm_reviews
        context['pcc_review'] = pcc_review
        context['paper'] = paper

    return render(request, 'app/report.html', context)

@login_required
def reupload_paper(request):
    # Handle file upload
    err = ''
    current_user = request.user
    sam2017_user = SAM2017User.objects.get(user=current_user)
    papers = Paper.objects.filter(contact_author=sam2017_user)

    if sam2017_user.user.has_perm('app.add_paper'):
        print('user has permission to add paper')
    else:
        print('user doesn''t have permission to upload paper')
    print("XYZ")
    if request.method == 'POST':
        print("If Passed")
        form = ReuploadForm(request.POST, request.FILES)
        if (form.is_valid() and Paper.isRightExt(request.FILES['docfile'].name)):
            oldPaper = Paper.objects.get(id=request.POST['id'])
            title = oldPaper.title
            authors = oldPaper.authors
            print(0)
            print(oldPaper)
            print(1)
            oldPaper.docfile = request.FILES['docfile']
            oldPaper.revision = True
            oldPaper.save()
            notification = Notification(
                    text = 'Paper '+title+' by '+authors+' resubmitted'
            )
            notification.save()
            spread_submitted_notification(notification, oldPaper, sam2017_user)
            return render(request, 'app/upload.html', {'papers': papers, 'form': DocumentForm(),'error_message':err})

        elif form.is_valid():
            err = 'The paper is not a PDF or Microsoft Word type.'
        else:
            err = 'form invalid'
            id = request.GET['id']
        # Redirect to the document list after POST
        return render(request, 'app/reupload.html', {'papers': papers, 'form': ReuploadForm(),'error_message':err})
    else:
        print("IF Failed")
        id = request.GET['id']
        form = ReuploadForm() # A empty, unbound form
    # Render list page with the documents and the form
    return render_to_response('app/reupload.html',{'form': form, 'id': id},context_instance=RequestContext(request))

def download(request, paper_id):
    paper = Paper.objects.get(pk=paper_id)
    extension = paper.docfile.url.rsplit('.')[1]
    file_name = paper.title + '.' + extension
    response = HttpResponse(paper.docfile, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="%s"' % file_name
    response['X-Sendfile'] = paper.docfile

    return response

def get_note_from_template(template, replacements):
    ret_string = template.text

    for replacement in replacements:
        ret_string = ret_string.replace(template.key, replacement, 1)

    return ret_string


def spread_submitted_notification(note, paper, author):
#   get all pccs
    pccs = SAM2017User.objects.filter(user__groups__name='PCC')
    for pcc in pccs:
        user_note = UserNotification (
            user = pcc,
            notification = note
        )
        user_note.save()

#   now save notification for submitter
    user_note = UserNotification (
            user = author,
            notification = note
    )
    user_note.save()

def spread_resolve_conflict_notification(note, pcms):

    for pcm in pcms:
        user_note = UserNotification (
            user = pcm,
            notification = note
        )
        user_note.save()

def spread_pcm_assign_notification(note, pcm_ids):

    for pcm_id in pcm_ids:
        user_note = UserNotification(
            user = SAM2017User.objects.get(pk = pcm_id),
            notification = note
        )
        user_note.save()

def spread_report_ready_notification(note):

    pccs = SAM2017User.objects.filter(user__groups__name='PCC')

    for pcc in pccs:
        user_note = UserNotification(
            user = pcc,
            notification = note
        )
        user_note.save()

def handle_notification(request):
    notification=dict()
    notes = UserNotification.objects.filter(user__user__id=request.user.id, viewed=False)
    for note in notes:
        notification[note.notification.id] = note.notification.text

    # get all deadlines that aren't stale
    # for each notification within the deadline object, get ones that haven't been touched in a day
    # and viewed = true
    deadlines = Deadline.objects.filter(date__gt=timezone.now(), notification__last_touched__lte=timezone.now()-datetime.timedelta(days=1), notification__viewed=True)
    # save them so that their datetime is set to now and set viewed = False
    for deadline in deadlines:
        deadline.notification.viewed = False
        deadline.save()
    # the notification will be picked up the next time around

    return JsonResponse(notification)

@login_required
def pcm_wish_list(request, paper_id):
    paperX = Paper.objects.get(pk=paper_id)
    error_message = ''

    if(PCMPickList.objects.filter(paper__id=paper_id, pcm__user__id=request.user.id).exists()):
        error_message = 'You have already preselected this paper'

    if(not Paper.pcm_is_not_author(SAM2017User.objects.get(user__id=request.user.id), paperX)):
        error_message = 'You dog! You can\'t select to review your own paper!'

    if request.method == 'POST':
        current_user = request.user
        sam2017_user = SAM2017User.objects.get(user=current_user)

        if request.POST['submit'] == 'Confirm':
            pcm_pick = PCMPickList(
                pcm = sam2017_user,
                paper = paperX
            )
            pcm_pick.save()

        return redirect('/app/')

    return render(request, 'app/wishlist.html', {'paper': paperX, 'error_message': error_message})
