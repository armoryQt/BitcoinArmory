################################################################################
#                                                                              #
# Copyright (C) 2011-2014, Armory Technologies, Inc.                           #
# Distributed under the GNU Affero General Public License (AGPL v3)            #
# See LICENSE or http://www.gnu.org/licenses/agpl.html                         #
#                                                                              #
################################################################################

from PyQt4.Qt import * #@UnusedWildImport
from PyQt4.QtGui import * #@UnusedWildImport
from py2exe import resources
from armoryengine.ArmoryUtils import LOGINFO, USE_TESTNET
from ui.Frames import NewWalletFrame, SetPassphraseFrame, VerifyPassphraseFrame,\
   WalletBackupFrame
from qtdefines import GETFONT
from armoryengine.PyBtcWallet import PyBtcWallet
from CppBlockUtils import SecureBinaryData

# This class is intended to be an abstract Wizard class that
# will hold all of the functionality that is common to all 
# Wizards in Armory. 
class ArmoryWizard(QWizard):
   def __init__(self, parent, main):
      super(QWizard, self).__init__(parent)
      self.parent = parent
      self.main   = main
      self.setFont(GETFONT('var'))
      self.setWindowFlags(Qt.Window)
      # Need to adjust the wizard frame size whenever the page changes.
      self.connect(self, SIGNAL('currentIdChanged(int)'), self.fitContents)
      if USE_TESTNET:
         self.setWindowTitle('Armory - Bitcoin Wallet Management [TESTNET]')
         self.setWindowIcon(QIcon(':/armory_icon_green_32x32.png'))
      else:
         self.setWindowTitle('Armory - Bitcoin Wallet Management')
         self.setWindowIcon(QIcon(':/armory_icon_32x32.png'))
   
   def fitContents(self):
      self.adjustSize()

# This class is intended to be an abstract Wizard Page class that
# will hold all of the functionality that is common to all 
# Wizard pages in Armory. 
# The layout is QVBoxLayout and holds a single QFrame (self.pageFrame)
class ArmoryWizardPage(QWizardPage):
   def __init__(self, wizard, pageFrame):
      super(ArmoryWizardPage, self).__init__(wizard)
      self.pageFrame = pageFrame
      self.pageLayout = QVBoxLayout()
      self.pageLayout.addWidget(self.pageFrame)
      self.setLayout(self.pageLayout)
   
   # override this method to implement validators
   def validatePage(self):
      return True

################################ Wallet Wizard ################################
# Wallet Wizard has these pages:
#     1. Create Wallet
#     2. Set Passphrase
#     3. Verify Passphrase
#     4. Unlock Wallet
#     5. Create Paper Backup
#     6. Create Watcing Only Wallet
#     7. Summary
class WalletWizard(ArmoryWizard):
   def __init__(self, parent, main):
      super(WalletWizard,self).__init__(parent, main)
      self.newWallet = None
      self.setWindowTitle(self.tr("Wallet Wizard"))
      
      # Page 1: Create Wallet
      self.walletCreationPage = WalletCreationPage(self)
      self.addPage(self.walletCreationPage)
      
      # Page 2: Set Passphrase
      self.setPassphrasePage = SetPassphrasePage(self)
      self.addPage(self.setPassphrasePage)
      
      # Page 3: Verify Passphrase
      self.verifyPassphrasePage = VerifyPassphrasePage(self)
      self.addPage(self.verifyPassphrasePage)
      
      # Page 4: Create Paper Backup
      self.walletBackupPage = WalletBackupPage(self)
      self.addPage(self.walletBackupPage)
      
      # Page 5: Create Watching Only Wallet
      self.createWatchingOnlyWalletPage = CreateWatchingOnlyWalletPage(self)
      self.addPage(self.createWatchingOnlyWalletPage)
      
      # Page 6: Summary
      self.summaryPage = SummaryPage(self)
      self.addPage(self.summaryPage)

      self.setButtonLayout([QWizard.BackButton,
         QWizard.Stretch,
         QWizard.NextButton,
         QWizard.FinishButton])

   def initializePage(self, *args, **kwargs):

      if self.currentPage() == self.verifyPassphrasePage:
         self.verifyPassphrasePage.setPassphrase(
               self.setPassphrasePage.pageFrame.getPassphrase())
      elif self.currentPage() == self.walletBackupPage:
         self.newWallet = PyBtcWallet().createNewWallet( \
                        securePassphrase=self.setPassphrasePage.pageFrame.getPassphrase(), \
                        kdfTargSec=self.walletCreationPage.pageFrame.getKdfSec(), \
                        kdfMaxMem=self.walletCreationPage.pageFrame.getKdfBytes(), \
                        shortLabel=self.walletCreationPage.pageFrame.getName(), \
                        longLabel=self.walletCreationPage.pageFrame.getDescription(), \
                        doRegisterWithBDM=False)
         self.newWallet.unlock(securePassphrase=
                  SecureBinaryData(self.setPassphrasePage.pageFrame.getPassphrase()))
         self.walletBackupPage.pageFrame.setWallet(self.newWallet)
         
   def cleanupPage(self, *args, **kwargs):
      if self.currentPage() == self.walletBackupPage:
         self.newWallet = None
   
class WalletCreationPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletCreationPage, self).__init__(wizard,
            NewWalletFrame(wizard, wizard.main, "Create Wallet"))
      self.setTitle(self.tr("Step 1: Create Wallet"))
      self.setSubTitle(self.tr("""
            Create a new wallet for managing your funds.
            The name and description can be changed at any time."""))

class SetPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SetPassphrasePage, self).__init__(wizard, 
               SetPassphraseFrame(wizard, wizard.main, "Set Passphrase", self.updateNextButton))
      self.setTitle(self.tr("Step 2: Set Passphrase"))
      self.setSubTitle(self.tr("Set Passphrase <Subtitle>"))
      self.updateNextButton()

   def updateNextButton(self):
      self.emit(SIGNAL("completeChanged()"))
   
   def isComplete(self):
      return self.pageFrame.checkPassphrase(False)
   
class VerifyPassphrasePage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(VerifyPassphrasePage, self).__init__(wizard, 
            VerifyPassphraseFrame(wizard, wizard.main, "Verify Passphrase"))
      self.passphrase = None
      self.setTitle(self.tr("Step 3: Verify Passphrase"))
      self.setSubTitle(self.tr("Verify Passphrase <Subtitle>"))
   
   def setPassphrase(self, passphrase):
      self.passphrase = passphrase        
   
   def validatePage(self):
      result = self.passphrase == str(self.pageFrame.edtPasswd3.text())
      if not result:
         QMessageBox.critical(self, 'Invalid Passphrase', \
            'You entered your confirmation passphrase incorrectly!', QMessageBox.Ok)
      return result
      
class WalletBackupPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(WalletBackupPage, self).__init__(wizard,
                                WalletBackupFrame(wizard, wizard.main, "Backup Wallet"))
      self.setTitle(self.tr("Step 4: Backup Wallet"))
      self.setSubTitle(self.tr("Backup wallet <Subtitle>"))

class CreateWatchingOnlyWalletPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(CreateWatchingOnlyWalletPage, self).__init__(wizard, QFrame())
      self.setTitle(self.tr("Step 5: Watching Only Wallet"))
      self.setSubTitle(self.tr("Watching Only wallet <Subtitle>"))
      
class SummaryPage(ArmoryWizardPage):
   def __init__(self, wizard):
      super(SummaryPage, self).__init__(wizard, QFrame())
      self.setTitle(self.tr("Step 6: Wallet Creation Summary"))
      self.setSubTitle(self.tr("Wallet Creation Summary <Subtitle>"))
